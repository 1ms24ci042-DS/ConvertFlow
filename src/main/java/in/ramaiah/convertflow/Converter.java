package in.ramaiah.convertflow;

import java.util.Map;

public final class Converter {
    private Converter() {}
    private static final Map<String, Double> LENGTH = Map.of("m", 1.0, "km", 1000.0, "mi", 1609.344, "ft", 0.3048);
    private static final Map<String, Double> MASS = Map.of("kg", 1.0, "g", 0.001, "lb", 0.45359237);
    public static double convert(String from, String to, double value) {
        if (!Double.isFinite(value)) throw new IllegalArgumentException("Value must be finite");
        if (from == null || to == null) throw new IllegalArgumentException("from and to are required");
        double result;
        if (LENGTH.containsKey(from) && LENGTH.containsKey(to)) result = value * LENGTH.get(from) / LENGTH.get(to);
        else if (MASS.containsKey(from) && MASS.containsKey(to)) result = value * MASS.get(from) / MASS.get(to);
        else if (isTemperature(from) && isTemperature(to)) {
            double celsius = switch (from) { case "c" -> value; case "f" -> (value - 32) * 5 / 9; default -> value - 273.15; };
            if (celsius < -273.15) throw new IllegalArgumentException("Temperature is below absolute zero");
            result = switch (to) { case "c" -> celsius; case "f" -> celsius * 9 / 5 + 32; default -> celsius + 273.15; };
        } else throw new IllegalArgumentException("Unsupported or incompatible units");
        if (!Double.isFinite(result)) throw new IllegalArgumentException("Result is outside the supported range");
        return result;
    }
    private static boolean isTemperature(String unit) { return unit.equals("c") || unit.equals("f") || unit.equals("k"); }
}
