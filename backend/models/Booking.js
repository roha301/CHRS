const mongoose = require('mongoose');

const bookingSchema = new mongoose.Schema({
    user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    hall: { type: mongoose.Schema.Types.ObjectId, ref: 'Hall', required: true },
    date: { type: Date, required: true },
    startTime: { type: String, required: true }, // Format "HH:mm"
    endTime: { type: String, required: true },   // Format "HH:mm"
    purpose: { type: String, required: true },
    status: { 
        type: String, 
        enum: ['Pending', 'Approved', 'Rejected'], 
        default: 'Pending' 
    },
    qrCode: { type: String }, // Base64 or path to QR code image
    posterData: { type: Object } // Data for event poster generation
}, { timestamps: true });

module.exports = mongoose.model('Booking', bookingSchema);
