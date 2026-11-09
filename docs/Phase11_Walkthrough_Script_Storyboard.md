# SceneLock - optional walkthrough (2 minutes 50 seconds maximum)

**Format:** Screen recording with your own voice, showing the real SceneLock
interface. The brief recommends a video of no more than three minutes.
The following is a recording script and storyboard, **not a video or evidence
that a live Gemini call occurred**.

| Timestamp | Screen action | Voiceover (adapt naturally, do not just read) |
|---|---|---|
| 0:00-0:20 | Show title and short screenshot of screenplay/prompt mismatch. | "I'm Aditya Gautam. I built SceneLock for Kuku's Problem 3. It helps an AI video artist catch important screenplay-to-prompt mistakes before generating expensive footage." |
| 0:20-0:42 | Open SceneLock; point to screenplay, prompt and shot selector. | "The input is one screenplay beat, the proposed video prompt and the scope of the planned shot. This matters because a reaction close-up should not be forced to show every earlier story action." |
| 0:42-1:05 | Click **Load Sample** or paste the prepared fictional Meera/Arjun handover case. Select shot type and intent. | "Here a screenplay says Arjun gives a red envelope to Meera, while the prompt reverses the handover." |
| 1:05-1:35 | **If Gemini is genuinely configured:** press **Analyse Prompt** and record the actual waiting/result. **If not:** press **Open Offline Demo (No Gemini)** and keep its warning legible. | **Live branch:** "The model proposes structured facts, which Python checks against the original text before anything appears." **Offline branch:** "I do not have a live Gemini result here. This clearly labeled human-authored fixture demonstrates the review workflow, not AI accuracy." |
| 1:35-1:58 | Expand one issue card; highlight source quotes, severity and minimum suggestion. | "An issue links the exact screenplay wording to the exact prompt wording. Missing details do not get invented prompt quotations. Invalid evidence is rejected." |
| 1:58-2:18 | Select **Accept Suggestion**, then edit the separately editable corrected prompt. | "The artist still controls the creative decision. Their response is saved separately so it cannot rewrite the original model finding." |
| 2:18-2:34 | Click **Download JSON** and **Download CSV**; briefly show file contents. | "The export keeps scene facts, evidence, review decisions and the revised prompt. Raw AI output is a separate artifact if a real model call ran." |
| 2:34-2:50 | Show the final QA report/baseline summary and limitations. | "All 187 software tests passed, but Gemini accuracy is not measured without authenticated evaluations. The keyword baseline made real shot-scope and role-direction mistakes; these guide the next live tests." |

### Recording preparation

1. For a live demonstration, configure the key privately and run the full
   workflow once **before** recording. Model results can vary: use and describe
   only what actually appears.
2. If Gemini is unavailable, keep the offline fixture label visible. Do not
   say it is a model prediction or cut the video to imply a live inference.
3. Rehearse the click sequence. Keep the video around **2:40-2:50** with
   narration and pauses; do not exceed **3:00**.
4. Use screen recording and voiceover in QuickTime, OBS or a tool you already
   know. Do not include the Google API-key setup page, secrets, private tabs,
   billing account, or actual confidential screenplay data in the recording.
5. Upload the final recording as an unlisted YouTube video, Loom link, or
   viewable Drive file. Verify that anyone with the link can watch without
   requesting access. The link does not exist until you actually upload it.

### Alternate case if the model response is clean

Do not manufacture an issue card. Explain that the fresh input returned
"No Significant Issues Detected" and show a second, genuinely processed
contradictory case if you have sufficient quota. Offline fixtures can
demonstrate UI behavior but must stay explicitly labeled synthetic.
