package in.ramaiah.convertflow;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Executors;

public final class App {
    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getenv().getOrDefault("APP_PORT", "8080"));
        HttpServer server = createServer(port);
        server.start();
        Runtime.getRuntime().addShutdownHook(new Thread(() -> server.stop(2)));
        System.out.println("ConvertFlow listening on port " + server.getAddress().getPort());
    }
    static HttpServer createServer(int port) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 0);
        server.createContext("/", App::handle);
        server.setExecutor(Executors.newFixedThreadPool(8, r -> { Thread t = new Thread(r); t.setDaemon(true); return t; }));
        return server;
    }
    private static void handle(HttpExchange exchange) throws IOException {
        try {
            if (!exchange.getRequestMethod().equals("GET")) {
                exchange.getResponseHeaders().set("Allow", "GET");
                reply(exchange, 405, "{\"error\":\"Only GET is supported\"}"); return;
            }
            switch (exchange.getRequestURI().getPath()) {
                case "/" -> reply(exchange, 200, "{\"application\":\"ConvertFlow\",\"version\":\"1.0.0\",\"usage\":\"/convert?from=km&to=mi&value=5\"}");
                case "/health" -> reply(exchange, 200, "{\"status\":\"UP\"}");
                case "/convert" -> {
                    Map<String, String> q = query(exchange.getRequestURI().getRawQuery());
                    if (!q.containsKey("value")) throw new IllegalArgumentException("value is required");
                    double value;
                    try { value = Double.parseDouble(q.get("value")); }
                    catch (NumberFormatException e) { throw new IllegalArgumentException("value must be numeric"); }
                    double result = Converter.convert(q.get("from"), q.get("to"), value);
                    reply(exchange, 200, "{\"from\":\"" + q.get("from") + "\",\"to\":\"" + q.get("to") + "\",\"value\":" + value + ",\"result\":" + result + "}");
                }
                default -> reply(exchange, 404, "{\"error\":\"Endpoint not found\"}");
            }
        } catch (IllegalArgumentException e) {
            reply(exchange, 400, "{\"error\":\"" + e.getMessage() + "\"}");
        } finally { exchange.close(); }
    }
    private static Map<String, String> query(String raw) {
        Map<String, String> values = new HashMap<>();
        if (raw == null) return values;
        for (String part : raw.split("&")) {
            String[] pair = part.split("=", 2);
            if (pair.length != 2) throw new IllegalArgumentException("Malformed query parameter");
            String key = URLDecoder.decode(pair[0], StandardCharsets.UTF_8);
            String value = URLDecoder.decode(pair[1], StandardCharsets.UTF_8);
            if (values.putIfAbsent(key, value) != null) throw new IllegalArgumentException("Duplicate query parameter");
        }
        return values;
    }
    private static void reply(HttpExchange exchange, int status, String json) throws IOException {
        byte[] body = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        exchange.sendResponseHeaders(status, body.length);
        exchange.getResponseBody().write(body);
    }
}
