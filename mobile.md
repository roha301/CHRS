# Android Application Development Prompt: KKWIEER CHRS

This document contains a comprehensive prompt that you can use with AI coding assistants (like ChatGPT, Claude, or GitHub Copilot) or give to a developer to recreate the **College Hall Reservation System (CHRS)** as a native Android mobile application.

---

## 🚀 The Prompt

**Title**: Create a Native Android App for College Hall Reservation System (CHRS)

**Context**: 
I have an existing web-based "College Hall Reservation System" for KKWIEER. I want to build a "same as it is" native Android application using **Kotlin** (preferred) or **Java** in **Android Studio**. The app should be high-performance, modern, and follow Material Design 3 guidelines while maintaining the "Glassmorphism" aesthetic of the web version.

**Technical Stack**:
- **Language**: Kotlin (with Coroutines/Flow) or Java.
- **Architecture**: MVVM (Model-View-ViewModel).
- **UI Framework**: Jetpack Compose (Modern) or XML Layouts (Traditional).
- **Networking**: Retrofit 2 with GSON for API interaction.
- **Authentication**: Firebase Authentication or Google Sign-In SDK (restricted to @kkwagh.edu.in).
- **Images/Icons**: Coil/Glide for image loading and FontAwesome/Material Icons.
- **Utils**: ZXing or ML Kit for QR Code scanning.

**Key Features to Implement**:

1.  **Authentication Module**:
    - **Student Login**: Exclusive "Sign in with Google" restricted to `@kkwagh.edu.in` domain.
    - **Admin Login**: Username/Password based login.
    - **Registration**: Simple admin registration form with password confirmation.
    - **Session Management**: Persistent login using EncryptedSharedPreferences.

2.  **Dashboard**:
    - Overview cards showing "Total Bookings", "Active Events", and "Available Halls".
    - Recent activity feed.
    - Glassmorphism effect for cards.

3.  **Hall Management**:
    - List view of all college halls with images, capacity, and amenities.
    - Search and filter functionality.
    - Detail view for each hall.

4.  **Booking System**:
    - Calendar-based booking interface.
    - Slot selection (Date/Time) with conflict detection.
    - Booking status tracking (Pending, Approved, Rejected).

5.  **Event Management & QR System**:
    - List of upcoming events.
    - **Event Registration**: Form for students to register for events.
    - **QR Check-in**: 
        - **Admin mode**: Built-in QR scanner to scan student tickets.
        - **Student mode**: Display personal QR code/ticket for check-in.
    - Self-check-in feature using location/geo-fencing (Optional but recommended).

6.  **Profile & Settings**:
    - User profile details.
    - Dark/Light mode toggle.
    - Account management.

**Design Requirements**:
- **Aesthetics**: Premium, clean, and professional. Use "Inter" and "Poppins" fonts.
- **Colors**: Deep blues, vibrant primary accents, and subtle gradients.
- **Interactions**: Smooth transitions between fragments/screens. Use Lottie animations for loading/success states.
- **Layout**: Bottom Navigation Bar for main sections (Home, Halls, Events, Profile).

**Instructions for Output**:
1. Provide the `build.gradle` (Module:app) dependencies.
2. Outline the Folder Structure (Data, Domain, UI).
3. Generate the core UI code for the Login Screen and Dashboard.
4. Implement the Retrofit API Interface matching a standard REST backend.
5. Provide the QR Scanning logic using ML Kit.

---

## 📂 Suggested Folder Structure
```text
com.kkwieer.chrs/
├── data/
│   ├── api/          # Retrofit interfaces
│   ├── model/        # Data classes (User, Hall, Booking)
│   └── repository/   # Data handling logic
├── ui/
│   ├── auth/         # Login & Register Activities/Screens
│   ├── dashboard/    # Main landing screen
│   ├── halls/        # Hall listing and details
│   ├── bookings/     # Booking logic
│   ├── events/       # Event management & QR Logic
│   └── theme/        # Color, Type, Shape definitions
└── utils/            # QR Helper, Date Formatter, Extensions
```

## 🛠️ Implementation Steps for Android Studio
1. **Initialize Project**: Create a "New Project" -> "Empty Compose Activity" (or Empty Views Activity).
2. **Add Dependencies**: Copy the dependencies from the generated prompt output into your `build.gradle`.
3. **Setup Auth**: Configure Google Cloud Console for the `@kkwagh.edu.in` SHA-1 key.
4. **Backend Integration**: Ensure your Android app points to your hosted API URL (e.g., `https://chrs-api.yourdomain.com`).
