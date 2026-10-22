package in.ramaiah.convertflow;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ConverterTest {
    @Test void kilometresToMiles() { assertEquals(3.106855961, Converter.convert("km", "mi", 5), 1e-8); }
    @Test void kilogramsToPounds() { assertEquals(2.20462262, Converter.convert("kg", "lb", 1), 1e-8); }
    @Test void temperature() { assertEquals(32, Converter.convert("c", "f", 0), 1e-9); assertEquals(0, Converter.convert("k", "c", 273.15), 1e-9); }
    @Test void identityAndZero() { assertEquals(7, Converter.convert("ft", "ft", 7), 1e-9); assertEquals(0, Converter.convert("g", "kg", 0), 1e-9); }
    @Test void rejectsDifferentDimensions() { assertThrows(IllegalArgumentException.class, () -> Converter.convert("m", "kg", 1)); }
    @Test void rejectsNonFiniteInput() { assertThrows(IllegalArgumentException.class, () -> Converter.convert("m", "km", Double.NaN)); }
    @Test void rejectsInvalidTemperature() { assertThrows(IllegalArgumentException.class, () -> Converter.convert("k", "c", -1)); }
    @Test void rejectsOverflow() { assertThrows(IllegalArgumentException.class, () -> Converter.convert("km", "m", Double.MAX_VALUE)); }
}
