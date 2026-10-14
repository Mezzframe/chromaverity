# Glossary

| Term | Meaning here |
|---|---|
| **ADR** | Architecture Decision Record: a one-page note of a decision and why. Ours live in `docs/adr/` |
| **Agent** | An AI model that calls tools in a loop (e.g. Claude Code). chromaverity is one of its tools |
| **ABR ladder** | The set of resolutions and bitrates a streaming service encodes one programme into, so players can switch between them |
| **BRNG** | `signalstats` figure: share of pixels outside broadcast range |
| **Bitstream filter (bsf)** | FFmpeg component that edits encoded data without decoding it; used for lossless retagging |
| **BT.601 / BT.709 / BT.2020** | ITU-R recommendations for SD, HD and UHD/wide-gamut video. Each defines primaries and a Y'CbCr matrix |
| **Chroma siting** | Where subsampled chroma samples sit relative to luma (`left`, `topleft`, ...) |
| **Chroma subsampling** | Storing color (chroma) at lower resolution than brightness (luma), e.g. 4:2:0 keeps one chroma sample per 2×2 luma block. Eyes notice brightness detail more than color detail |
| **Code value** | The integer stored for each sample in the file (0-255 at 8-bit) |
| **colr box** | The MP4/MOV container's own copy of the color flags. It can disagree with the flags inside the video bitstream (the VUI); ffprobe and most players read the box first |
| **Container vs bitstream** | The container (MP4, MKV, MXF) is the wrapper that holds streams and metadata; the bitstream is the encoded video inside it. Color flags live in both, and either can be wrong |
| **Convert** | A fix that changes the pixels (re-encode with a `scale` filter) to match a label that's right. Costs a generation of quality. Compare **Retag** |
| **CRF** | Constant Rate Factor: x264/x265's quality dial. Lower is better quality and a bigger file; 16-18 is near-transparent |
| **Confidence** | How strongly the evidence supports a CT3xx verdict: high / medium / low |
| **CT ID** | Stable finding code. CT stands for "color tag" (the project's working name was colortruth). CT1xx label lint, CT2xx diff, CT3xx essence |
| **Essence** | The picture (and sound) itself, as opposed to metadata about it |
| **Frame sync** | Broadcast box that re-times an incoming video signal to the house clock; it also forces the signal's format, which is why plants don't have label problems and files do |
| **Footroom / headroom** | Code values below black (16) and above white (235) in limited range |
| **Full range ("pc")** | Black at 0, white at 255 (8-bit) |
| **H.273** | ITU-T standard that numbers the primaries/transfer/matrix code points used by H.264, HEVC, AV1 |
| **HDR10** | PQ transfer + BT.2020 primaries + 10-bit, usually with static metadata |
| **HLG** | Hybrid Log-Gamma, an HDR transfer from BBC/NHK (ARIB STD-B67) |
| **Hop** | Any step that rewrites a file: transcode, export, upscale, package |
| **Legal range / broadcast range** | The code values a broadcaster accepts: roughly limited range plus a small overshoot (EBU R 103 allows about -5% to +105%). `BRNG` measures what's outside it |
| **Label / tags** | The color metadata a file carries about itself |
| **Limited range ("tv")** | Black at 16, white at 235 (8-bit luma) |
| **Luma / chroma** | The brightness part (Y') and the two color-difference parts (Cb, Cr) of a Y'CbCr signal |
| **Mastering display / MaxCLL / MaxFALL** | HDR10 static metadata: the display the content was graded on, the brightest pixel (MaxCLL) and the brightest frame average (MaxFALL). Travels as side data and is often dropped by transcodes |
| **Matrix** | Coefficients that turn R'G'B' into Y'CbCr. FFmpeg calls it `color_space` |
| **MCP** | Model Context Protocol: a standard way for AI agents to call tools |
| **Mislabel zoo** | Our synthetic set of clips with deliberately wrong labels and known truth |
| **Muxer / demuxer** | FFmpeg's names for the container writer and reader. `-f null` is a muxer that writes nothing |
| **NLE** | Non-linear editor: Premiere, Resolve, Final Cut, Avid |
| **OETF / EOTF** | The two halves of a transfer function. OETF: scene light to code values, in the camera. EOTF: code values to light, in the display. "Gamma" is the everyday word for both |
| **PQ** | Perceptual Quantizer, SMPTE ST 2084; the HDR10 transfer |
| **PLUGE** | Test signal with bars slightly below and above black, used to set monitor black level |
| **Primaries** | The exact red, green and blue a color space is built on |
| **Reserved codes** | 0 and 255 (8-bit) in limited range, kept for SDI timing reference signals |
| **Re-encode / generation loss** | Decoding and encoding again. Every pass through a lossy codec loses a little; "a generation" is one such pass |
| **Retag** | Change the label without touching the pixels (a bitstream filter rewrites the flags, `-c copy` keeps the video). Lossless and quick. Compare **Convert** |
| **SDI / ST 2110** | The baseband video standards of a broadcast plant: SDI over coax, ST 2110 over IP. In both, the format is enforced by the plant, so labels can't drift the way they do in files |
| **SDR / HDR** | Standard and High Dynamic Range. SDR uses the BT.709 transfer; HDR uses PQ or HLG and usually BT.2020 primaries at 10-bit |
| **Side data** | Extra per-frame or per-stream metadata that travels beside the pixels (HDR static metadata, for instance). ffprobe lists it under `side_data_list` |
| **signalstats** | FFmpeg filter that measures luma/chroma statistics per frame |
| **Spine check** | Mezzframe's review habit: before shipping, say what you found and decided on four axes. NET (network exposure), SEC (security), CLOUD/ML (reproducibility, data, models), DELIVERY (tests, docs, done-ness). "Lite" is one line per axis; "standard" adds must/should/could items. The PR template carries the table |
| **Stream copy** | `-c copy`: pass the encoded stream through untouched. No decode, no quality change |
| **Transfer (OETF/EOTF)** | The curve between light and code values ("gamma"); BT.709, PQ, HLG |
| **VUI** | Video Usability Information: the part of an H.264/HEVC header that carries the color flags |
| **Work order (WO)** | A numbered task list for one piece of maintenance, written for Claude Code to carry out and Mark to review commit by commit. Kept in `docs/work-orders/` |
| **Y'CbCr** | The way video stores color: one brightness channel (Y') and two color-difference channels (Cb, Cr), instead of R, G and B. The prime marks mean "after the transfer curve" |
| **Markers** | ⟨assumption⟩ believed, not measured · ⟨verify⟩ changes over time, check before relying on it · ⟨should⟩ a known gap we intend to close · ⟨PRO⟩ needs a professional (lawyer, accountant) before it can be settled |

Spelling: "color" everywhere, matching the FFmpeg and H.273 names it mirrors (`color_range`, `-colorspace`), and "labelled" throughout.