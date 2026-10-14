# Security Policy / Güvenlik Politikası

## Supported Versions

| Version | Supported |
|---|---|
| Main / Release Branch | :white_check_mark: |
| Legacy Prototypes | :x: |

---

## Reporting a Vulnerability / Güvenlik Açığı Bildirimi

If you discover a security issue or privacy concern (such as unintended frame persistence, memory leaks, or network transmission during booth runs):

1. Please do not open public GitHub issues.
2. Report vulnerabilities privately to the project maintainers with a reproducible scenario.
3. Include your environment details (OS, Python version, camera hardware index).

---

## Privacy Architecture / Gizlilik Mimarisi

- **Local Inference**: The application runs the bundled MediaPipe and ONNX models locally on CPU and does not implement visitor video uploads. See the README for the optional operator-configured LAN camera bridge.
- **In-Memory Buffering**: Camera frames are processed on-the-fly and immediately overwritten or discarded. No visitor face biometric embeddings or video snippets are saved to disk in standard operation.
