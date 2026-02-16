/**
 * PCM Recorder Processor - AudioWorklet for microphone capture
 * Captures audio from microphone and sends to main thread
 *
 * This runs on the audio rendering thread for low-latency processing
 */

class PCMRecorderProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.frameCount = 0;
    }

    /**
     * Process audio frames
     * Called automatically by Web Audio API (~128 samples at a time)
     */
    process(inputs, outputs, parameters) {
        const input = inputs[0];

        if (input && input.length > 0) {
            // Get mono channel (first channel)
            const inputChannel = input[0];

            // Copy buffer to avoid recycled memory issues
            const inputCopy = new Float32Array(inputChannel);

            // Send to main thread
            this.port.postMessage(inputCopy);

            this.frameCount++;
        }

        // Return true to keep processor alive
        return true;
    }
}

// Register processor
registerProcessor('pcm-recorder-processor', PCMRecorderProcessor);
