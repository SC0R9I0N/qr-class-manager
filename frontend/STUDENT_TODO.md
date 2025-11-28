# Student Interface - TODO for Team Partners

The frontend is complete. Backend integration and deployment tasks remain.

---

## Already Completed (Frontend)

- Student login with Cognito authentication
- Camera-based QR code scanning
- Manual QR code input fallback
- Attendance success screen
- Responsive UI design
- Error handling

---

## HIGH PRIORITY - Backend Integration

### 1. Create Student Account in Cognito
- [ ] Create user in Cognito User Pool `us-east-1_z61jO4Mni`
- [ ] Email: `student1@example.com`
- [ ] Password: `StrongPass123!`

**Assigned To:** _____________

---

### 2. Connect to Real Backend API
- [ ] Open `src/pages/student/StudentAttendancePage.tsx`
- [ ] Change line 13: `USE_MOCK_DATA = false`
- [ ] Test attendance submission works

**API Endpoint:**
```
POST https://7ql71igsye.execute-api.us-east-1.amazonaws.com/prod/attendance/scan
Authorization: Bearer <JWT_ID_TOKEN>
Body: {"qr_data": "{...}", "student_email": "student1@example.com"}
```

**Assigned To:** _____________

---

### 3. Update Backend Lambda
- [ ] Review `lambdas/scan-attendance/lambda_function.py`
- [ ] Verify it validates JWT token
- [ ] Verify it checks QR code expiry
- [ ] Test it writes to DynamoDB

**Assigned To:** _____________

---

### 4. Configure CORS
- [ ] Update API Gateway CORS settings
- [ ] Allow `Authorization` and `Content-Type` headers
- [ ] Set `Access-Control-Allow-Origin` for frontend domain

**Assigned To:** _____________

---

## MEDIUM PRIORITY - Testing & Deployment

### 5. Test End-to-End Flow
- [ ] Student logs in
- [ ] Student scans QR code
- [ ] Attendance is recorded
- [ ] Success screen appears

**Assigned To:** _____________

---

### 6. Deploy to Production
- [ ] Run `npm run build`
- [ ] Deploy to AWS Amplify/Vercel/S3
- [ ] Ensure HTTPS is enabled (required for camera)
- [ ] Test production build

**Assigned To:** _____________

---

### 7. Test on Mobile
- [ ] Test on iPhone Safari
- [ ] Test on Android Chrome
- [ ] Verify camera works
- [ ] Verify UI is responsive

**Assigned To:** _____________

---

## LOW PRIORITY - Optional Improvements

### 8. Add Features (Optional)
- [ ] GET /student/attendance-history endpoint
- [ ] GET /student/classes endpoint
- [ ] Visual feedback on QR scan success
- [ ] Loading animations

**Assigned To:** _____________

---

## Quick Reference

**Frontend URL:** `http://localhost:5173`

**Student Routes:**
- `/` - Login
- `/student` - Login
- `/attendance` - QR Scanner

**Test Credentials:**
- Email: `student1@example.com`
- Password: `StrongPass123!`

**Backend API:**
- URL: `https://7ql71igsye.execute-api.us-east-1.amazonaws.com/prod`
- Endpoint: `/attendance/scan`

**Cognito:**
- Pool ID: `us-east-1_z61jO4Mni`
- Client ID: `6pfufvg52tejjmoa03rigpev8i`

**Key Files:**
- `src/pages/student/StudentAttendancePage.tsx` (mock mode flag)
- `src/components/student/StudentLoginForm.tsx`
- `src/components/student/QRScanner.tsx`
- `lambdas/scan-attendance/lambda_function.py`

---

## Team Assignments

**Frontend:** Reuben (DONE)  
**Backend Integration:** _____________  
**Testing:** _____________  
**Deployment:** _____________

---

**Last Updated:** November 28, 2025  
**Status:** Frontend Complete | Backend Integration Pending
