/**
 * PCM Player Processor - AudioWorklet for audio playback
 * Uses ring buffer to handle variable network latency
 *
 * This runs on the audio rendering thread for smooth, glitch-free playback
 */

class PCMPlayerProcessor extends AudioWorkletProcessor {
    constructor() {
        super();

        // Ring buffer configuration
        // 24kHz × 180 seconds = ~4.3 million samples (large buffer for network jitter)
        this.bufferSize = 24000 * 180;
        this.buffer = new Float32Array(this.bufferSize);
        this.writeIndex = 0;  // Where we write new data
        this.readIndex = 0;   // Where we read for playback

        // Handle incoming audio data from main thread
        this.port.onmessage = (event) => {
            // Check for special commands
            if (event.data.command === 'clear') {
                // Clear buffer by jumping read to write position
                this.readIndex = this.writeIndex;
                return;
            }

            // Decode Int16 or Float32 array from ArrayBuffer
            let samples;

            if (event.data instanceof ArrayBuffer) {
                // Try Int16 first (from Google TTS)
                const int16Samples = new Int16Array(event.data);
                samples = new Float32Array(int16Samples.length);

                // Convert Int16 to Float32 [-1.0, 1.0]
                for (let i = 0; i < int16Samples.length; i++) {
                    samples[i] = int16Samples[i] / 32768.0;
                }
            } else if (event.data instanceof Float32Array) {
                // Already Float32
                samples = event.data;
            } else {
                console.error('Unknown audio data type:', typeof event.data);
                return;
            }

            // Add to ring buffer
            this._enqueue(samples);
        };
    }

    /**
     * Add audio samples to ring buffer
     */
    _enqueue(samples) {
        for (let i = 0; i < samples.length; i++) {
            // Store sample at write position
            this.buffer[this.writeIndex] = samples[i];

            // Move write index forward (wrap around at buffer end)
            this.writeIndex = (this.writeIndex + 1) % this.bufferSize;

            // Overflow protection: if write catches up to read, move read forward
            // This overwrites oldest unplayed samples (rare, only under extreme delay)
            if (this.writeIndex === this.readIndex) {
                this.readIndex = (this.readIndex + 1) % this.bufferSize;
            }
        }
    }

    /**
     * Process audio for playback
     * Called automatically by Web Audio API
     */
    process(inputs, outputs, parameters) {
        const output = outputs[0];
        const framesPerBlock = output[0].length;

        // Play buffered audio
        for (let frame = 0; frame < framesPerBlock; frame++) {
            const sample = this.buffer[this.readIndex];

            // Write to output channels (mono to stereo)
            output[0][frame] = sample;  // Left channel
            if (output.length > 1) {
                output[1][frame] = sample;  // Right channel (duplicate)
            }

            // Move read index forward unless buffer is empty
            if (this.readIndex !== this.writeIndex) {
                this.readIndex = (this.readIndex + 1) % this.bufferSize;
            }
            // If readIndex === writeIndex, we're out of data - output silence (0.0)
        }

        // Return true to keep processor alive
        return true;
    }
}

// Register processor
registerProcessor('pcm-player-processor', PCMPlayerProcessor);
