# Streamlit live demo and README video

This guide covers a **Streamlit Community Cloud demo** of TripPilot. It does not require an Azure subscription and does not create Azure resources. The Azure walkthrough remains a separate deployment option; a Streamlit demo is not evidence of an Azure deployment.

## 1. Correct the deployment form

Use these exact deployment settings:

| Field | Value |
|---|---|
| Repository | `yazdanparasthesam/llm-zoomcamp` |
| Branch | `main` |
| Main file path | **`Capstone3-tripilot/app.py`** |
| App URL | Keep the suggested name, or choose an available name such as `tripilot-capstone3` |
| Advanced settings → Python version | **3.11** |
| Advanced settings → Secrets | **Leave empty for the first deployment** |

The main-file path is relative to the **repository root**. `streamlit_app.py` is not the entrypoint in this project. Do not rename `app.py` just to match the form's suggestion.

Alternatively, click **Paste GitHub URL** and paste:

<https://github.com/yazdanparasthesam/llm-zoomcamp/blob/main/Capstone3-tripilot/app.py>

Keep `Capstone3-tripilot/requirements.txt` beside `app.py`; do not move it to the course-repository root. Community Cloud searches the entrypoint directory for dependency files. Choose Python 3.11 to match the tested project environment and its pinned dependencies.

Click **Save** in Advanced settings, then **Deploy**. A green “Domain is available” message only confirms that the name is available; it does not mean the app is already deployed.

## 2. First launch: no-key mode

For the first launch, keep Secrets empty. The app should use its clearly labelled **offline mock mode**, committed review/route snapshots, and SQLite telemetry. You can exercise retrieval, citations, tool outputs, itinerary rendering, feedback, and the Monitoring tab without a paid model API.

Community Cloud does not launch the project's Docker Compose stack. PostgreSQL, Elasticsearch, and Grafana are not automatically deployed alongside this app. SQLite files and in-memory sessions should be treated as temporary, not durable hosted storage.

If deployment fails, inspect **Manage app → Logs** and share the error text without credentials. Do not change dependency pins before checking the selected Python version and actual error.

For later live Groq use, first ensure the current client-compatibility update has also been committed to GitHub. The pinned OpenAI 1.35.1 / HTTPX 0.28.1 combination requires the compatible client initialization supplied by the current project. A README-only update does not modify application code. Add any real key only through **Community Cloud Settings → Secrets**, never in Git, the README, a screenshot, or the recording. Verify actual non-mock output and model access before calling it live inference.

## 3. Add the real live-demo URL

After the app opens successfully:

1. Copy its actual HTTPS `streamlit.app` URL from the browser.
2. Open `Capstone3-tripilot/README.md` on GitHub and click the pencil/Edit button.
3. Replace the pending Live demo text with a Markdown link to that URL.
4. Preview the README and test the link before committing.

For example, replace the capitalized placeholder below with the **actual deployed URL**; do not publish it unchanged:

```markdown
> 🌐 **Live demo:** [Open TripPilot](YOUR_ACTUAL_STREAMLIT_HTTPS_URL)<br>
> 📹 **Demo video:** See the recording below.
```

Do not use another project's demo URL or assume a suggested subdomain is live. Send the actual URL after deployment so the project documentation can be finalized accurately.

## 4. Record your own TripPilot demo

A short 30–60 second recording is enough to show:

1. The deployed URL and TripPilot's visible model mode.
2. One travel request with origin, destination, month, trip length, and flight budget.
3. The hotel recommendation and review citations.
4. The structured itinerary or tool trace.
5. Feedback submission and the Monitoring tab.

Record the app window, not an entire desktop containing credentials or billing pages. Leave the mock-mode label visible if that is the mode used. Use your own TripPilot recording and links.

GitHub supports MP4, MOV, and WebM videos. H.264 MP4 has the broadest browser compatibility. For repositories owned by a free GitHub account, keep the uploaded video under **10 MB**; paid-plan owners have a larger allowance. If your recording is too large, trim or compress it before uploading.

## 5. Embed the video player near the top of the README

1. Open `Capstone3-tripilot/README.md` in GitHub's web editor.
2. Put the cursor on an empty line beneath the Demo video callout and above the banner/table of contents.
3. Drag your MP4/WebM into the editor and wait for the upload to finish.
4. Keep the generated GitHub attachment URL on a **line by itself, outside the blockquote and outside a code fence**. The usual URL begins with `https://github.com/user-attachments/assets/`.
5. Remove the pending video text and the insertion comment, preview the rendered player, then commit.

If your editor does not accept the video directly, upload it in a relevant issue or pull-request comment in **your own repository**, then copy its generated attachment URL into the README. Do not reuse the example project's attachment.

The resulting structure should be:

```markdown
> 🌐 **Live demo:** [Open TripPilot](YOUR_ACTUAL_STREAMLIT_HTTPS_URL)<br>
> 📹 **Demo video:**

YOUR_ACTUAL_GITHUB_VIDEO_ATTACHMENT_URL
```

Both uppercase placeholders must be replaced with real URLs. A `sandbox:` download link from this chat is not a public GitHub video URL.

## 6. What remains pending

The live-demo URL and video remain pending until they are published and verified. The README opening uses explicit pending labels rather than unverified links. After deployment, send the live URL and either your recording or its GitHub attachment URL.

Official references:

- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [Deployment form and Python settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Dependency-file discovery](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [GitHub media attachments and limits](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files)
