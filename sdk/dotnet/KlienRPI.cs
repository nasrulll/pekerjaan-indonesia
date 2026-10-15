using System;
using System.Net.Http;
using System.Threading.Tasks;
/** .NET 8+; klien sederhana baca-saja, tangani JSON sesuai model aplikasi. */
public sealed class KlienRPI {
    private static readonly HttpClient Http = new HttpClient { Timeout = TimeSpan.FromSeconds(15) };
    private readonly Uri asal;
    public KlienRPI(string alamat) {
        asal = new Uri(alamat, UriKind.Absolute);
        if (asal.Scheme != "https") throw new ArgumentException("Server publik harus HTTPS");
    }
    public Task<string> PekerjaanAsync(string nama) {
        var url = new Uri(asal, "/v1/pekerjaan?nama=" + Uri.EscapeDataString(nama));
        return Http.GetStringAsync(url);
    }
}
