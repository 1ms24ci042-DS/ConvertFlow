package in.ramaiah.convertflow;
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import com.sun.net.httpserver.HttpServer;
import java.net.URI;
import java.net.http.*;
class AppTest {
    static HttpServer server; static String base;
    static final HttpClient client = HttpClient.newHttpClient();
    @BeforeAll static void start() throws Exception { server = App.createServer(0); server.start(); base = "http://localhost:" + server.getAddress().getPort(); }
    @AfterAll static void stop() { server.stop(0); }
    private HttpResponse<String> get(String path) throws Exception { return client.send(HttpRequest.newBuilder(URI.create(base + path)).GET().build(), HttpResponse.BodyHandlers.ofString()); }
    @Test void health() throws Exception { var r=get("/health"); assertEquals(200,r.statusCode()); assertTrue(r.body().contains("UP")); }
    @Test void conversion() throws Exception { var r=get("/convert?from=km&to=m&value=5"); assertEquals(200,r.statusCode()); assertTrue(r.body().contains("5000.0")); }
    @Test void missingParameter() throws Exception { assertEquals(400,get("/convert?from=m&to=km").statusCode()); }
    @Test void badNumber() throws Exception { assertEquals(400,get("/convert?from=m&to=km&value=abc").statusCode()); }
    @Test void duplicateParameter() throws Exception { assertEquals(400,get("/convert?from=m&from=km&to=km&value=1").statusCode()); }
    @Test void unknownRoute() throws Exception { assertEquals(404,get("/missing").statusCode()); }
    @Test void methodNotAllowed() throws Exception { var r=client.send(HttpRequest.newBuilder(URI.create(base+"/health")).POST(HttpRequest.BodyPublishers.noBody()).build(),HttpResponse.BodyHandlers.ofString()); assertEquals(405,r.statusCode()); }
}
