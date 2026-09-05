This is the o
I am building an AI-driven mock interview and technical assessment platform.

Your task is to design the COMPLETE end-to-end working process of the system, from the moment a candidate uploads their resume until the final evaluation report is generated.



I want you to explain the actual SYSTEM WORKFLOW, including what happens at each stage, what data is produced, how that data moves to the next stage, what decisions are made, and how the final score/report is calculated.

The complete process should work as follows:

1. RESUME UPLOAD
- Candidate uploads a PDF or image resume.
- Explain how the system receives and validates the file.
- Explain what information needs to be extracted from it.
- The system should identify skills, experience, projects, tools, roles, and other relevant candidate information.
- Convert the unstructured resume into a structured candidate profile.

2. CANDIDATE PROFILE & ROLE MAPPING
- Use the extracted resume information to understand the candidate's technical background.
- Map the candidate's skills and experience to a standardized job role.
- Determine the relevant technologies, concepts, and competency areas for that role.
- Explain how the selected role, candidate profile, and difficulty level influence the rest of the assessment.

3. INTERVIEW CONFIGURATION
- Candidate selects or confirms the target job role and difficulty level.
- Build a personalized interview plan based on:
  - Target role
  - Difficulty
  - Resume skills
  - Candidate experience
  - Required technologies/concepts
- Determine what types of questions should be asked and in what sequence.
- Explain how the system avoids generating irrelevant or repetitive questions.

4. QUESTION SELECTION / GENERATION
- Select appropriate technical and conceptual questions based on the candidate's profile and target role.
- Include questions ranging from core concepts to advanced reasoning where appropriate.
- Explain how the system maintains the relationship between each question and its expected/reference answer.
- The system should know which competency each question evaluates.

5. LIVE AI INTERVIEW
- Start the interview and present questions to the candidate.
- Candidate can respond through voice/text.
- Capture each response and associate it with the exact question asked.
- Maintain interview state so the system knows:
  - Current question
  - Previous questions
  - Candidate responses
  - Remaining questions
  - Interview progress
- Explain how follow-up questions can be selected when the candidate's response requires clarification or deeper assessment.

6. ANSWER PROCESSING & TECHNICAL EVALUATION
- Convert spoken responses into text when necessary.
- Compare each candidate response against the expected/reference answer and relevant concepts.
- Evaluate conceptual relevance and technical accuracy.
- Generate a score for each answer.
- Store the reasoning/metrics behind the score so the final evaluation remains explainable.
- Aggregate individual question scores into the overall technical score.

7. BEHAVIORAL & COMMUNICATION ANALYSIS
- During the interview, independently analyze observable communication and behavioral indicators.
- Evaluate factors such as:
  - Eye direction/engagement
  - Facial orientation/movement
  - Speech rate
  - Pitch/tone variation
  - Pauses/hesitation
  - Other measurable communication indicators
- Do NOT make unsupported psychological or emotional claims.
- Generate separate behavioral and communication metrics.
- Explain how these metrics contribute to the final assessment.

8. CODING ASSESSMENT
- At the appropriate point in the interview, provide the candidate with a coding problem relevant to their role/programming language.
- Candidate writes code in an online coding environment.
- Submit the code for controlled execution.
- Test the solution against visible and hidden test cases.
- Capture:
  - Compilation status
  - Correctness
  - Test-case results
  - Runtime
  - Memory usage
  - Runtime errors
- Generate a coding score based on correctness and performance.
- Explain how the coding result connects to the candidate's overall technical assessment.

9. DATA AGGREGATION
After the interview and coding assessment are complete, collect all assessment data:

- Resume/profile information
- Role-fit information
- Question-level technical scores
- Overall technical score
- Coding score
- Communication metrics
- Behavioral metrics
- Interview completion/progress
- Strengths and weaknesses identified throughout the assessment

Explain exactly how these independent results are normalized and prepared for final scoring.

10. EXPLAINABLE FINAL SCORING
Create a transparent scoring model.

The final evaluation should contain separate dimensions such as:
- Technical Knowledge
- Coding Ability
- Role Fit
- Communication
- Behavioral Indicators

Define how weighted scores are combined into the final assessment.

The scoring must be explainable:
- Show where every score came from.
- Show the contribution of each assessment component.
- Avoid black-box decisions.
- Do not claim that the system can make a definitive hiring decision.

11. FEEDBACK GENERATION
Based on the complete assessment, identify:
- Strongest technical areas
- Weakest technical areas
- Coding strengths/weaknesses
- Communication strengths/weaknesses
- Behavioral observations
- Missing or weak skills relative to the target role
- Specific areas the candidate should improve

Recommendations must be directly connected to the assessment results rather than generic advice.

12. FINAL REPORT GENERATION
Generate a comprehensive candidate report containing:

- Candidate overview
- Target role
- Resume-derived skills
- Interview summary
- Technical performance
- Question-by-question results
- Coding assessment results
- Communication analysis
- Behavioral analysis
- Role-fit analysis
- Overall score
- Score breakdown
- Strengths
- Weaknesses
- Recommended improvements
- Final Fit status

The report should clearly explain HOW the final Fit status was reached.

13. COMPLETE DATA FLOW
Finally, provide the complete end-to-end data flow in one clear sequence:

Resume Upload
→ Resume Validation
→ Text Extraction
→ Candidate Profile
→ Skill/Role Mapping
→ Interview Configuration
→ Question Selection
→ Live Interview
→ Response Processing
→ Technical Evaluation
→ Behavioral/Communication Analysis
→ Coding Assessment
→ Score Aggregation
→ Explainable Final Scoring
→ Feedback Generation
→ Final PDF/JSON Report

For every stage, clearly specify:
1. Input
2. Processing
3. Output
4. Data passed to the next stage
5. What can fail
6. What should happen when it fails

The goal is to define the COMPLETE BUSINESS AND SYSTEM LOGIC of the platform, not its technology stack.

Make the workflow detailed enough that a developer can use it as the functional blueprint for implementing the entire application.