import java.nio.file.*; import java.util.*;

/** Interactive class demo. Pick a query, mark relevant and non-relevant results, see the updated query,
 *  the new ranking and before-and-after metrics. Usage: RocchioDemo <dataDir> */
public class RocchioDemo {
  static final int SHOW = 10, TOP = 1000;
  static Scanner in = new Scanner(System.in);

  static String ask(String prompt) {
    System.out.print(prompt); System.out.flush();
    if (!in.hasNextLine()) return null;
    String s = in.nextLine().trim();
    if (!System.getenv().getOrDefault("DEMO_ECHO", "").isEmpty()) System.out.println(s);   // shows typed input when run from a script
    return s;
  }
  static double num(String prompt, double dflt) {
    while (true) {
      String s = ask(prompt + " [" + dflt + "]: ");
      if (s == null || s.isEmpty()) return dflt;
      try { double v = Double.parseDouble(s); if (v >= 0) return v; } catch (NumberFormatException e) { }
      System.out.println("   Please type a number that is 0 or more, or press Enter for " + dflt + ".");
    }
  }
  static String cut(String s, int n) { return s.length() <= n ? s : s.substring(0, n - 3) + "..."; }
  static void show(RocchioCore c, List<String> r, List<String> old, Set<String> rel, boolean key) {
    for (int i = 0; i < Math.min(SHOW, r.size()); i++) {
      String d = r.get(i), move = "";
      if (old != null) { int p = old.indexOf(d); move = p < 0 ? "  new" : String.format("%+5d", p - i); }
      System.out.printf("%3d. %s doc %-5s%s %s%n", i + 1, key ? (rel.contains(d) ? "R" : "-") : " ", d, move, cut(c.titles.get(d), 62));
    }
  }
  static List<String> pick(String prompt, List<String> r, Collection<String> taken) {
    while (true) {
      List<String> out = new ArrayList<>();
      String s = ask(prompt);
      if (s == null || s.isEmpty()) return out;
      try {
        for (String n : s.split("[ ,]+")) {
          int rank = Integer.parseInt(n);
          if (rank < 1 || rank > SHOW) throw new NumberFormatException();
          String d = r.get(rank - 1);
          if (!out.contains(d) && !taken.contains(d)) out.add(d);
        }
        return out;
      } catch (NumberFormatException e) { System.out.println("   Please type rank numbers from 1 to " + SHOW + ", separated by spaces."); }
    }
  }
  static void compare(String label, List<String> before, List<String> after, Set<String> rel) {
    double[] a = RocchioCore.metrics(before, rel), b = RocchioCore.metrics(after, rel);
    System.out.println("\n" + label);
    System.out.printf("  %-18s %8s %8s %8s%n", "Metric", "Before", "After", "Change");
    for (int i = 0; i < a.length; i++)
      System.out.printf("  %-18s %8.4f %8.4f %+8.4f%n", RocchioCore.METRIC_NAMES[i], a[i], b[i], b[i] - a[i]);
  }

  public static void main(String[] x) throws Exception {
    java.util.logging.Logger.getLogger("org.apache.lucene").setLevel(java.util.logging.Level.OFF);
    RocchioCore c = new RocchioCore(Paths.get(x[0]));
    List<String> judged = new ArrayList<>(c.qrels.keySet());
    judged.sort(Comparator.comparingInt(Integer::parseInt));
    System.out.println("Rocchio relevance feedback on Cranfield (" + c.titles.size() + " documents, " + judged.size() + " judged queries)");
    System.out.println("Judged query IDs: " + String.join(" ", judged));
    while (true) {
      String id = ask("\nQuery ID (or q to quit): ");
      if (id == null || id.equalsIgnoreCase("q")) break;
      if (!c.qrels.containsKey(id)) { System.out.println("That query has no judgments. Pick one from the list."); continue; }
      Set<String> rel = c.qrels.get(id);
      System.out.println("\n1. ORIGINAL QUERY " + id + ": " + cut(c.queries.get(id), 300));
      Map<String, Double> q0 = c.queryVector(c.queries.get(id));
      List<String> r0 = c.search(q0, TOP + SHOW);
      System.out.println("\n   INITIAL RESULTS (top " + SHOW + ")");
      show(c, r0, null, rel, false);

      System.out.println("\n2. SELECT DOCUMENTS FOR FEEDBACK (type rank numbers, for example: 1 3 5)");
      List<String> good = pick("   Relevant ranks: ", r0, List.of());
      List<String> bad = pick("   Non-relevant ranks: ", r0, good);
      System.out.println("   Relevant documents: " + good);
      System.out.println("   Non-relevant documents: " + bad);

      while (true) {
        double a = num("\n   alpha", 1.0), b = num("   beta", 0.75), g = num("   gamma", 0.15);
        Map<String, Double> q1 = c.rocchio(q0, good, bad, a, b, g);
        System.out.printf("%n3. UPDATED QUERY: alpha=%.2f beta=%.2f gamma=%.2f: %d words before, %d after%n", a, b, g, q0.size(), q1.size());
        System.out.printf("   %-20s %8s %8s  %s%n", "Word (stemmed)", "Before", "After", "Change");
        q1.entrySet().stream().sorted((p, q) -> Double.compare(q.getValue(), p.getValue())).limit(12).forEach(e -> {
          double w0 = q0.getOrDefault(e.getKey(), 0.0);
          System.out.printf("   %-20s %8.4f %8.4f  %s%n", e.getKey(), w0, e.getValue(), w0 == 0 ? "added" : e.getValue() > w0 ? "raised" : e.getValue() < w0 ? "lowered" : "same");
        });
        List<String> gone = new ArrayList<>(q0.keySet()); gone.removeAll(q1.keySet());
        System.out.println("   Words removed: " + (gone.isEmpty() ? "none" : gone));

        List<String> r1 = c.search(q1, TOP + SHOW);
        System.out.println("\n4. NEW RESULTS (top " + SHOW + "; R = in answer key; +n = moved up n places)");
        show(c, r1, r0, rel, true);
        System.out.println("\n   ORIGINAL RESULTS WITH ANSWER KEY");
        show(c, r0, null, rel, true);

        System.out.println("\n5. BEFORE AND AFTER");
        compare("All documents", r0.subList(0, Math.min(TOP, r0.size())), r1.subList(0, Math.min(TOP, r1.size())), rel);
        Set<String> seen = new HashSet<>(good); seen.addAll(bad);
        Set<String> relLeft = new HashSet<>(rel); relLeft.removeAll(seen);
        List<String> u0 = new ArrayList<>(r0), u1 = new ArrayList<>(r1);
        u0.removeAll(seen); u1.removeAll(seen);
        if (relLeft.isEmpty()) System.out.println("\nUnseen documents: no relevant documents are left to measure.");
        else compare("Unseen documents only (selected documents removed)", u0.subList(0, Math.min(TOP, u0.size())), u1.subList(0, Math.min(TOP, u1.size())), relLeft);

        String again = ask("\nTry other alpha, beta, gamma on this query? (y/n): ");
        if (again == null || !again.equalsIgnoreCase("y")) break;
      }
    }
  }
}
