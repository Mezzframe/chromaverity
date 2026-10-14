# Glossary

| Term | Meaning here |
|---|---|
| **Agent** | An AI model that calls tools in a loop (e.g. Claude Code). chromaverity is one of its tools |
| **BRNG** | `signalstats` figure: share of pixels outside broadcast range |
| **Bitstream filter (bsf)** | FFmpeg component that edits encoded data without decoding it; used for lossless retagging |
| **BT.601 / BT.709 / BT.2020** | ITU-R recommendations for SD, HD and UHD/wide-gamut video. Each defines primaries and a Y'CbCr matrix |
| **Chroma siting** | Where subsampled chroma samples sit relative to luma (`left`, `topleft`, ...) |
| **Code value** | The integer stored for each sample in the file (0-255 at 8-bit) |
| **Confidence** | How strongly the evidence supports a CT3xx verdict: high / medium / low |
| **CT ID** | Stable finding code (CT1xx label lint, CT2xx diff, CT3xx essence) |
| **Essence** | The picture (and sound) itself, as opposed to metadata about it |
| **Footroom / headroom** | Code values below black (16) and above white (235) in limited range |
| **Full range ("pc")** | Black at 0, white at 255 (8-bit) |
| **H.273** | ITU-T standard that numbers the primaries/transfer/matrix code points used by H.264, HEVC, AV1 |
| **HDR10** | PQ transfer + BT.2020 primaries + 10-bit, usually with static metadata |
| **HLG** | Hybrid Log-Gamma, an HDR transfer from BBC/NHK (ARIB STD-B67) |
| **Hop** | Any step that rewrites a file: transcode, export, upscale, package |
| **Label / tags** | The color metadata a file carries about itself |
| **Limited range ("tv")** | Black at 16, white at 235 (8-bit luma) |
| **Matrix** | Coefficients that turn R'G'B' into Y'CbCr. FFmpeg calls it `color_space` |
| **MCP** | Model Context Protocol: a standard way for AI agents to call tools |
| **Mislabel zoo** | Our synthetic set of clips with deliberately wrong labels and known truth |
| **PQ** | Perceptual Quantizer, SMPTE ST 2084; the HDR10 transfer |
| **PLUGE** | Test signal with bars slightly below and above black, used to set monitor black level |
| **Primaries** | The exact red, green and blue a color space is built on |
| **Reserved codes** | 0 and 255 (8-bit) in limited range, kept for SDI timing reference signals |
| **Retag** | Change the label without touching the pixels |
| **signalstats** | FFmpeg filter that measures luma/chroma statistics per frame |
| **Transfer (OETF/EOTF)** | The curve between light and code values ("gamma"); BT.709, PQ, HLG |
| **VUI** | Video Usability Information: the part of an H.264/HEVC header that carries the color flags |
