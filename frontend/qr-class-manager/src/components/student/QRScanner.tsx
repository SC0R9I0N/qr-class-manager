import React, { useState, useEffect } from "react";
import { Html5QrcodeScanner } from "html5-qrcode";
import "./QRScanner.css";

interface QRScannerProps {
    studentName: string;
    studentEmail: string;
    onScanSuccess: (qrData: string) => void;
}

const QRScanner: React.FC<QRScannerProps> = ({ 
    studentName, 
    studentEmail, 
    onScanSuccess 
}) => {
    const [qrInput, setQrInput] = useState("");
    const [error, setError] = useState("");
    const [useCamera, setUseCamera] = useState(true);
    const [scanner, setScanner] = useState<Html5QrcodeScanner | null>(null);

    useEffect(() => {
        if (useCamera && !scanner) {
            const qrScanner = new Html5QrcodeScanner(
                "qr-reader",
                { 
                    fps: 10, 
                    qrbox: { width: 250, height: 250 },
                    aspectRatio: 1.0
                },
                false
            );

            qrScanner.render(
                (decodedText) => {
                    try {
                        // Validate that it's valid JSON
                        JSON.parse(decodedText);
                        qrScanner.clear();
                        onScanSuccess(decodedText);
                    } catch {
                        setError("Invalid QR code format. Please scan a valid attendance QR code.");
                    }
                },
                (errorMessage) => {
                    // Ignore continuous scanning errors (normal operation)
                    // Only log actual issues
                    if (!errorMessage.includes("NotFoundException")) {
                        console.debug("QR Scanner:", errorMessage);
                    }
                }
            );

            setScanner(qrScanner);
        }

        return () => {
            if (scanner) {
                scanner.clear().catch((err) => {
                    console.debug("Scanner cleanup:", err);
                });
            }
        };
    }, [useCamera, scanner, onScanSuccess]);

    const handleManualSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!qrInput.trim()) {
            setError("Please enter QR code data");
            return;
        }

        try {
            // Validate that it's valid JSON
            JSON.parse(qrInput);
            onScanSuccess(qrInput);
        } catch {
            setError("Invalid QR code data format");
        }
    };

    const toggleMode = () => {
        if (scanner) {
            scanner.clear().catch((err) => {
                console.debug("Scanner cleanup:", err);
            });
            setScanner(null);
        }
        setUseCamera(!useCamera);
        setError("");
    };

    return (
        <div className="qr-scanner-container">
            <div className="scanner-card">
                <h1>Welcome, {studentName}!</h1>
                <p className="email-display">{studentEmail}</p>
                
                <div className="scanner-section">
                    <h2>Scan QR Code</h2>
                    
                    {useCamera ? (
                        <div className="camera-section">
                            <p className="instruction">
                                Point your camera at the instructor's QR code
                            </p>
                            <div id="qr-reader"></div>
                            <button 
                                className="toggle-btn"
                                onClick={toggleMode}
                                type="button"
                            >
                                Switch to Manual Input
                            </button>
                        </div>
                    ) : (
                        <div className="manual-section">
                            <p className="instruction">
                                Enter the QR code data manually or enable camera
                            </p>
                            
                            <form onSubmit={handleManualSubmit}>
                                <div className="form-group">
                                    <label htmlFor="qrData">QR Code Data</label>
                                    <textarea
                                        id="qrData"
                                        value={qrInput}
                                        onChange={(e) => {
                                            setQrInput(e.target.value);
                                            setError("");
                                        }}
                                        placeholder='{"session_id":"...","class_id":"..."}'
                                        rows={5}
                                        required
                                    />
                                </div>
                                
                                <button type="submit" className="scan-btn">
                                    Submit Attendance
                                </button>
                            </form>
                            
                            <button 
                                className="toggle-btn"
                                onClick={toggleMode}
                                type="button"
                            >
                                Use Camera Instead
                            </button>
                        </div>
                    )}
                    
                    {error && <div className="error-message">{error}</div>}
                </div>
            </div>
        </div>
    );
};

export default QRScanner;
