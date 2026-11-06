import java.io.*; import java.nio.file.*; import java.util.*;
import org.apache.lucene.analysis.*; import org.apache.lucene.analysis.en.EnglishAnalyzer;
import org.apache.lucene.analysis.tokenattributes.CharTermAttribute;
import org.apache.lucene.document.*; import org.apache.lucene.index.*; import org.apache.lucene.search.*;
import org.apache.lucene.search.similarities.*; import org.apache.lucene.store.*;

/** Part C: indexes Cranfield once, then runs each retrieval model on the same index and queries.
 *  Usage: LuceneExperiment <dataDir> <resultsDir> */
public class LuceneExperiment {
  static final String F = "contents";
  static final int DEPTH = 1000;
  static Analyzer an = new EnglishAnalyzer();

  static List<String> analyze(String s) throws IOException {
    List<String> o = new ArrayList<>();
    try (TokenStream ts = an.tokenStream(F, s)) {
      CharTermAttribute c = ts.addAttribute(CharTermAttribute.class);
      ts.reset();
      while (ts.incrementToken()) o.add(c.toString());
      ts.end();
    }
    return o;
  }

  static Query orQuery(List<String> toks) {
    BooleanQuery.Builder b = new BooleanQuery.Builder();
    for (String t : toks) b.add(new TermQuery(new Term(F, t)), BooleanClause.Occur.SHOULD);
    return b.build();
  }

  public static void main(String[] a) throws Exception {
    Path data = Paths.get(a[0]), res = Paths.get(a[1]);
    Directory dir = new ByteBuffersDirectory();
    try (IndexWriter w = new IndexWriter(dir, new IndexWriterConfig(an))) {
      for (String l : Files.readAllLines(data.resolve("docs.tsv"))) {
        String[] p = l.split("\t", -1);
        Document d = new Document();
        d.add(new StringField("id", p[0], Field.Store.YES));
        d.add(new TextField(F, p[2].isEmpty() ? p[1] : p[2], Field.Store.NO)); // text already opens with the title
        w.addDocument(d);
      }
    }
    IndexReader reader = DirectoryReader.open(dir);
    try (PrintWriter w = new PrintWriter(res.resolve("index_stats.txt").toFile())) {
      w.printf(Locale.ROOT, "lucene=%s docs=%d vocab=%d tokens=%d meanLen=%.2f%n", org.apache.lucene.util.Version.LATEST, reader.numDocs(),
        MultiTerms.getTerms(reader, F).size(), reader.getSumTotalTermFreq(F), (double) reader.getSumTotalTermFreq(F) / reader.numDocs());
    }
    List<String[]> Q = new ArrayList<>();
    for (String l : Files.readAllLines(data.resolve("queries.tsv"))) Q.add(l.split("\t", -1));

    Map<String, Similarity> sims = new LinkedHashMap<>();
    sims.put("TF-IDF", new ClassicSimilarity());
    sims.put("BM25", new BM25Similarity(1.2f, 0.75f));
    sims.put("LM-Dirichlet", new LMDirichletSimilarity(2000f));
    // Sensitivity variants, reported separately from the default-parameter comparison.
    for (float mu : new float[]{50f, 100f, 200f, 500f, 1000f}) sims.put("LMD-mu" + (int) mu, new LMDirichletSimilarity(mu));
    for (float l : new float[]{0.1f, 0.3f, 0.7f}) sims.put("LMJM-l" + l, new LMJelinekMercerSimilarity(l));
    for (float b : new float[]{0.25f, 0.5f, 1.0f}) sims.put("BM25-b" + b, new BM25Similarity(1.2f, b));

    StoredFields sf = reader.storedFields();
    for (var e : sims.entrySet()) {
      IndexSearcher s = new IndexSearcher(reader);
      s.setSimilarity(e.getValue());
      try (PrintWriter w = new PrintWriter(res.resolve("partc_" + e.getKey() + ".run").toFile())) {
        for (String[] q : Q) {
          ScoreDoc[] h = s.search(orQuery(analyze(q[2])), DEPTH).scoreDocs;
          for (int i = 0; i < h.length; i++)
            w.printf(Locale.ROOT, "%s Q0 %s %d %.6f %s%n", q[0], sf.document(h[i].doc).get("id"), i + 1, h[i].score, e.getKey());
        }
      }
    }
    reader.close();
  }
}
