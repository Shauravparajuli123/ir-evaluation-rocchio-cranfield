import java.io.*; import java.nio.file.*; import java.util.*;

/** Batch experiment. The answer key plays the user: among the top k results, documents in the key are
 *  marked relevant and the rest non-relevant. Usage: RocchioExperiment <dataDir> <resultsDir> <gridDir> */
public class RocchioExperiment {
  static final int TOP = 1020;   // leaves 1000 results after removing up to 20 seen documents

  static void run(RocchioCore c, List<String> qids, Map<String, List<String>> base, Path file, String tag,
                  double a, double b, double g, int k, PrintWriter changes) throws Exception {
    try (PrintWriter w = new PrintWriter(file.toFile())) {
      for (String q : qids) {
        List<String> seen = base.get(q).subList(0, Math.min(k, base.get(q).size()));
        List<String> rel = new ArrayList<>(), non = new ArrayList<>();
        for (String d : seen) (c.qrels.get(q).contains(d) ? rel : non).add(d);
        Map<String, Double> q0 = c.queryVector(c.queries.get(q));
        Map<String, Double> q1 = c.rocchio(q0, rel, non, a, b, g);
        List<String> r = c.search(q1, TOP);
        for (int i = 0; i < r.size(); i++) w.printf("%s Q0 %s %d 0 %s%n", q, r.get(i), i + 1, tag);
        if (changes != null) {
          long added = q1.keySet().stream().filter(t -> !q0.containsKey(t)).count();
          long removed = q0.keySet().stream().filter(t -> !q1.containsKey(t)).count();
          StringBuilder top = new StringBuilder();
          q1.entrySet().stream().filter(e -> !q0.containsKey(e.getKey())).sorted((x, y) -> Double.compare(y.getValue(), x.getValue())).limit(8)
            .forEach(e -> top.append(String.format(Locale.ROOT, "%s:%.3f ", e.getKey(), e.getValue())));
          changes.printf("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s%n", q, rel.size(), non.size(), q0.size(), q1.size(), added, removed, top.toString().trim());
        }
      }
    }
  }

  public static void main(String[] x) throws Exception {
    java.util.logging.Logger.getLogger("org.apache.lucene").setLevel(java.util.logging.Level.OFF);
    RocchioCore c = new RocchioCore(Paths.get(x[0]));
    Path res = Paths.get(x[1]), grid = Paths.get(x[2]);
    List<String> qids = new ArrayList<>(c.qrels.keySet());
    qids.sort(Comparator.comparingInt(Integer::parseInt));

    Map<String, List<String>> base = new HashMap<>();
    try (PrintWriter w = new PrintWriter(res.resolve("rocchio_original.run").toFile())) {
      for (String q : qids) {
        List<String> r = c.search(c.queryVector(c.queries.get(q)), TOP);
        base.put(q, r);
        for (int i = 0; i < r.size(); i++) w.printf("%s Q0 %s %d 0 original%n", q, r.get(i), i + 1);
      }
    }
    try (PrintWriter ch = new PrintWriter(res.resolve("query_changes.tsv").toFile())) {
      ch.println("qid\trel_in_top10\tnon_in_top10\torig_terms\tnew_terms\tadded\tremoved\ttop_added");
      run(c, qids, base, res.resolve("rocchio_updated.run"), "a1_b0.75_g0.15", 1, .75, .15, 10, ch);
    }
    try (PrintWriter ch = new PrintWriter(res.resolve("query_changes_gamma1.tsv").toFile())) {
      ch.println("qid\trel_in_top10\tnon_in_top10\torig_terms\tnew_terms\tadded\tremoved\ttop_added");
      run(c, qids, base, grid.resolve("gamma1_check.tmp"), "gamma1", 1, .75, 1, 10, ch);
    }
    double[] A = {0, .5, 1, 2}, B = {0, .25, .5, .75, 1, 1.5}, G = {0, .15, .25, .5, 1};
    for (double a : A) for (double b : B) for (double g : G) {
      if (a == 0 && b == 0) continue;     // would leave an empty query
      String tag = String.format(Locale.ROOT, "a%s_b%s_g%s_k10", a, b, g);
      run(c, qids, base, grid.resolve(tag + ".run"), tag, a, b, g, 10, null);
    }
    for (int k : new int[]{3, 5, 20}) {
      String tag = String.format(Locale.ROOT, "a1.0_b0.75_g0.15_k%d", k);
      run(c, qids, base, grid.resolve(tag + ".run"), tag, 1, .75, .15, k, null);
    }
  }
}
