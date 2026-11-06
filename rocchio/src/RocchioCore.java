import java.io.*; import java.nio.file.*; import java.util.*;
import org.apache.lucene.analysis.*; import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.analysis.tokenattributes.CharTermAttribute;
import org.apache.lucene.document.*; import org.apache.lucene.index.*; import org.apache.lucene.search.*;
import org.apache.lucene.search.similarities.ClassicSimilarity; import org.apache.lucene.store.*;

/** Shared code: builds the Part C index (Cranfield, EnglishAnalyzer, TF-IDF), holds the TF-IDF vectors,
 *  applies the Rocchio formula, and searches with a query vector. */
public class RocchioCore {
  static final String FIELD = "contents";
  final Analyzer analyzer = new EnglishAnalyzer();
  final Map<String, String> titles = new LinkedHashMap<>();
  final Map<String, String> queries = new LinkedHashMap<>();
  final Map<String, Set<String>> qrels = new HashMap<>();
  final Map<String, Map<String, Double>> docVectors = new HashMap<>();
  final Map<String, Double> idf = new HashMap<>();
  IndexReader reader; IndexSearcher searcher; StoredFields stored;

  RocchioCore(Path data) throws Exception {
    Directory dir = new ByteBuffersDirectory();
    Map<String, List<String>> tokens = new HashMap<>();
    try (IndexWriter w = new IndexWriter(dir, new IndexWriterConfig(analyzer))) {
      for (String line : Files.readAllLines(data.resolve("docs.tsv"))) {
        String[] p = line.split("\t", -1);          // id, title, abstract
        titles.put(p[0], p[1]);
        Document d = new Document();
        d.add(new StringField("id", p[0], Field.Store.YES));
        String body = p[2].isEmpty() ? p[1] : p[2];  // the abstract already opens with the title
        d.add(new TextField(FIELD, body, Field.Store.NO));
        w.addDocument(d);
        tokens.put(p[0], analyze(body));
      }
    }
    reader = DirectoryReader.open(dir);
    searcher = new IndexSearcher(reader);
    searcher.setSimilarity(new ClassicSimilarity());
    stored = reader.storedFields();
    int n = reader.numDocs();
    for (var e : tokens.entrySet())
      for (String t : e.getValue())
        idf.computeIfAbsent(t, k -> { try {
          return Math.log((n + 1.0) / (reader.docFreq(new Term(FIELD, k)) + 1.0)) + 1.0;   // Lucene's TF-IDF idf
        } catch (IOException x) { throw new RuntimeException(x); } });
    for (var e : tokens.entrySet()) {
      Map<String, Integer> tf = new HashMap<>();
      for (String t : e.getValue()) tf.merge(t, 1, Integer::sum);
      Map<String, Double> v = new HashMap<>();
      double norm = 1.0 / Math.sqrt(Math.max(1, e.getValue().size()));
      for (var f : tf.entrySet()) v.put(f.getKey(), Math.sqrt(f.getValue()) * idf.get(f.getKey()) * norm);   // Lucene's document weight
      docVectors.put(e.getKey(), unit(v));
    }
    for (String line : Files.readAllLines(data.resolve("queries.tsv"))) {
      String[] p = line.split("\t", -1); queries.put(p[0], p[2]);   // position ID, number in the file, text
    }
    for (String line : Files.readAllLines(data.resolve("qrels.txt"))) {
      String[] p = line.trim().split("\\s+");
      if (Integer.parseInt(p[3]) > 0) qrels.computeIfAbsent(p[0], k -> new HashSet<>()).add(p[2]);
    }
  }

  List<String> analyze(String text) throws IOException {
    List<String> out = new ArrayList<>();
    try (TokenStream ts = analyzer.tokenStream(FIELD, text)) {
      CharTermAttribute word = ts.addAttribute(CharTermAttribute.class);
      ts.reset();
      while (ts.incrementToken()) out.add(word.toString());
      ts.end();
    }
    return out;
  }

  static Map<String, Double> unit(Map<String, Double> v) {
    double s = 0; for (double x : v.values()) s += x * x;
    double len = Math.sqrt(s);
    Map<String, Double> o = new HashMap<>();
    if (len > 0) for (var e : v.entrySet()) o.put(e.getKey(), e.getValue() / len);
    return o;
  }

  /** Original query vector: count of each word times its idf, scaled to length 1. */
  Map<String, Double> queryVector(String text) throws IOException {
    Map<String, Double> v = new HashMap<>();
    for (String t : analyze(text))
      if (idf.containsKey(t)) v.merge(t, idf.get(t), Double::sum);    // words in no document are dropped
    return unit(v);
  }

  /** Rocchio: q' = alpha*q + beta*(mean of relevant docs) - gamma*(mean of non-relevant docs).
   *  Words whose final weight is zero or negative are removed. */
  Map<String, Double> rocchio(Map<String, Double> q, Collection<String> rel, Collection<String> non,
                              double alpha, double beta, double gamma) {
    Map<String, Double> o = new HashMap<>();
    q.forEach((t, w) -> o.merge(t, alpha * w, Double::sum));
    if (!rel.isEmpty()) for (String d : rel)
      docVectors.get(d).forEach((t, w) -> o.merge(t, beta * w / rel.size(), Double::sum));
    if (!non.isEmpty()) for (String d : non)
      docVectors.get(d).forEach((t, w) -> o.merge(t, -gamma * w / non.size(), Double::sum));
    o.values().removeIf(w -> w <= 1e-12);
    return o;
  }

  /** Lucene's TF-IDF score is (boost * idf) * (doc weight), so boost = query weight / idf
   *  makes the score equal to the dot product of the two vectors. */
  List<String> search(Map<String, Double> q, int top) throws IOException {
    BooleanQuery.Builder b = new BooleanQuery.Builder();
    q.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(e -> b.add(
        new BoostQuery(new TermQuery(new Term(FIELD, e.getKey())), (float) (e.getValue() / idf.get(e.getKey()))),
        BooleanClause.Occur.SHOULD));
    List<String> out = new ArrayList<>();
    for (ScoreDoc h : searcher.search(b.build(), top).scoreDocs) out.add(stored.document(h.doc).get("id"));
    return out;
  }

  // ---- metrics for the live demo (same definitions as ir_metrics.py) ----
  static double[] metrics(List<String> r, Set<String> rel) {
    int hits = 0, h10 = 0, h3 = 0; double sumP = 0, rr = 0, dcg = 0;
    for (int i = 0; i < r.size(); i++) if (rel.contains(r.get(i))) {
      hits++; sumP += (double) hits / (i + 1);
      if (rr == 0) rr = 1.0 / (i + 1);
      if (i < 10) { h10++; dcg += 1 / log2(i + 2); }
      if (i < 3) h3++;
    }
    double idcg = 0; for (int i = 0; i < Math.min(10, rel.size()); i++) idcg += 1 / log2(i + 2);
    double n = Math.max(1, rel.size());
    double p = r.isEmpty() ? 0 : (double) hits / r.size(), R = hits / n;
    double p10 = h10 / 10.0, r10 = h10 / n;
    return new double[]{p, R, f1(p, R), h3 / 3.0, p10, r10, f1(p10, r10), sumP / n, rr, idcg > 0 ? dcg / idcg : 0};
  }
  static final String[] METRIC_NAMES = {"Precision (list)", "Recall (list)", "F1 (list)", "P@3", "P@10", "Recall@10", "F1@10", "AP", "RR", "nDCG@10"};
  static double f1(double p, double r) { return p + r > 0 ? 2 * p * r / (p + r) : 0; }
  static double log2(double x) { return Math.log(x) / Math.log(2); }
}
