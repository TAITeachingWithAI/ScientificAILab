# Scientific AI Laboratory

An AI-powered inquiry laboratory for science education.

## Project

Teachers upload a confidential dossier describing an unknown scientific sample and the conditions of the investigation.

Students design experiments to characterize the sample.

The AI acts as a laboratory simulator, providing realistic experimental observations without revealing the identity of the sample.

## Current version

Version 0.1

## Setup

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure an AI provider. Copy `.env.example` to `.env` and fill in **one**
   provider's API key. For a free classroom setup, `gemini` or `groq` both have
   a free tier; `ollama` runs a local model with no key at all.

   ```
   LAB_PROVIDER=gemini
   GEMINI_API_KEY=your-key-here
   ```

   The key stays server-side — students never see it or need one of their own.

3. Run the app:

   ```
   streamlit run app.py
   ```

Then, as the **Teacher**, upload a dossier `.docx`; as a **Student**, design
experiments and read the simulated observations.

## TAI Erasmus + Project

- Andrea Lopez Incera
- Mirte van der Eyden

## Status

🚧 Under development