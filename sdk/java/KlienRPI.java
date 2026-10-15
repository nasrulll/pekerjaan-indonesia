import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
/** Java 17+; hasil JSON berupa teks agar tidak memaksakan pustaka JSON tertentu. */
public final class KlienRPI {
  private final URI asal;
  private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
  public KlienRPI(String asal) {
    this.asal = URI.create(asal);
    if (!"https".equals(this.asal.getScheme())) throw new IllegalArgumentException("Server publik harus HTTPS");
  }
  public String pekerjaan(String nama) throws Exception {
    URI uri=asal.resolve("/v1/pekerjaan?nama="+URLEncoder.encode(nama,StandardCharsets.UTF_8));
    var req=HttpRequest.newBuilder(uri).timeout(Duration.ofSeconds(15)).GET().build();
    var res=http.send(req,HttpResponse.BodyHandlers.ofString());
    if (res.statusCode()!=200) throw new IllegalStateException("HTTP "+res.statusCode());
    return res.body();
  }
}
