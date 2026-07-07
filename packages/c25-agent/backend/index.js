import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { errorHandler } from './middleware/errorHandler.js';

// Import routes
import arxivRoutes from './routes/arxiv.js';
import graphqlRoutes from './routes/graphql.js';
import weatherRoutes from './routes/weather.js';
import authRoutes from './routes/authentication.js';
import uploadRoutes from './routes/upload.js';
import searchRoutes from './routes/search.js';
import paymentRoutes from './routes/payment.js';

// ES module equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files from uploads directory
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Mount routes
app.use('/api/arxiv', arxivRoutes);
app.use('/api/graphql', graphqlRoutes);
app.use('/api/weather', weatherRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/search', searchRoutes);
app.use('/api/payment', paymentRoutes);

// Health check endpoint
app.get('/health', (_req, res) => {
    res.json({ status: 'OK', timestamp: new Date() });
});

// Root endpoint
app.get('/', (_req, res) => {
    res.json({ 
        name: 'C25 Agent API',
        version: '1.0.0',
        endpoints: {
            health: '/health',
            api: '/api'
        }
    });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Start server
const server = app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
    console.log(`Health check available at http://localhost:${PORT}/health`);
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (err) => {
    console.error('Unhandled Promise Rejection:', err);
    server.close(() => {
        process.exit(1);
    });
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received. Shutting down gracefully...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

export default app;
