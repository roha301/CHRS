const mongoose = require('mongoose');

const hallSchema = new mongoose.Schema({
    name: { type: String, required: true, unique: true },
    location: { type: String, required: true },
    capacity: { type: Number, required: true },
    resources: [{ type: String }],
    image: { type: String, default: 'https://via.placeholder.com/300x200?text=College+Hall' }
}, { timestamps: true });

module.exports = mongoose.model('Hall', hallSchema);
