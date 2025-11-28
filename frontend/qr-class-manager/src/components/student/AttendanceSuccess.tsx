import React from "react";
import "./AttendanceSuccess.css";

interface AttendanceSuccessProps {
    studentName: string;
    className: string;
    sessionDate: string;
    downloadUrl?: string;
    onDownload?: () => void;
}

const AttendanceSuccess: React.FC<AttendanceSuccessProps> = ({
    studentName,
    className,
    sessionDate,
    downloadUrl,
    onDownload
}) => {
    return (
        <div className="success-container">
            <div className="success-card">
                <div className="checkmark-circle">
                    <div className="checkmark">✓</div>
                </div>
                
                <h1>Attendance Recorded!</h1>
                <p className="success-message">
                    Your attendance has been successfully marked.
                </p>
                
                <div className="details-section">
                    <div className="detail-item">
                        <span className="label">Student:</span>
                        <span className="value">{studentName}</span>
                    </div>
                    <div className="detail-item">
                        <span className="label">Class:</span>
                        <span className="value">{className}</span>
                    </div>
                    <div className="detail-item">
                        <span className="label">Date:</span>
                        <span className="value">{sessionDate}</span>
                    </div>
                </div>
                
                {downloadUrl && (
                    <div className="download-section">
                        <h2>Lecture Materials Available</h2>
                        <p className="download-instruction">
                            Download today's lecture materials below:
                        </p>
                        <button 
                            className="download-btn"
                            onClick={onDownload || (() => window.open(downloadUrl, '_blank'))}
                        >
                            📥 Download Materials
                        </button>
                    </div>
                )}
                
                <button 
                    className="done-btn"
                    onClick={() => window.location.reload()}
                >
                    Done
                </button>
            </div>
        </div>
    );
};

export default AttendanceSuccess;
