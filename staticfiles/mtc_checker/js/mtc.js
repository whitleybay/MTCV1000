document.addEventListener('DOMContentLoaded', () => {
    const questionTextEl = document.getElementById('question-text');
    const answerInputEl = document.getElementById('answer-input');
    const keypadBtns = document.querySelectorAll('.keypad-btn');
    const questionCounterEl = document.getElementById('question-counter');
    const timeLeftDisplayEl = document.getElementById('time-left-display');
    const messageAreaEl = document.getElementById('message-area');
    // const testContainerEl = document.querySelector('.test-container'); // Not strictly used in current logic but good to have if needed

    const TIME_PER_QUESTION = 6; // seconds
    const PAUSE_BETWEEN_QUESTIONS = 3; // seconds
    
    // These should be defined globally by the script tag in test_interface.html
    // const practiceQuestions = /* ... */;
    // const mainQuestions = /* ... */;
    // const numTotalMainQuestions = /* ... */;
    // const submitUrl = /* ... */;
    // const testCompleteUrlTemplate = /* ... */;

    const NUM_PRACTICE_QUESTIONS = practiceQuestions.length;


    let currentQuestionIndex = 0;
    let currentQuestionSet = 'practice'; // 'practice' or 'main'
    let questions = practiceQuestions; // Start with practice questions
    let score = 0;
    let timerInterval;
    let timeLeft = TIME_PER_QUESTION;
    let answeredQuestionsData = [];
    let questionStartTime;

    function showElements(showMainTestArea) {
        if (showMainTestArea) {
            if (questionTextEl.parentElement) questionTextEl.parentElement.style.display = 'flex';
            answerInputEl.style.display = 'inline-block';
            const keypadEl = document.querySelector('.keypad');
            if (keypadEl) keypadEl.style.display = 'grid';
            messageAreaEl.style.display = 'none';
        } else {
            if (questionTextEl.parentElement) questionTextEl.parentElement.style.display = 'none';
            answerInputEl.style.display = 'none';
            const keypadEl = document.querySelector('.keypad');
            if (keypadEl) keypadEl.style.display = 'none';
            messageAreaEl.style.display = 'flex'; // Use flex for vertical centering of message
        }
    }

    function displayMessage(message, durationMs = 2000, callbackAfterMessage) {
        messageAreaEl.textContent = message;
        showElements(false); // Hide test area, show message area
        if (durationMs > 0) {
            setTimeout(() => {
                if (callbackAfterMessage) {
                    callbackAfterMessage();
                } else {
                    showElements(true); // Default: show main test elements after message
                }
            }, durationMs);
        }
        // If durationMs is 0, the message stays until manually changed.
    }

    function startTimer() {
        timeLeft = TIME_PER_QUESTION;
        questionStartTime = Date.now();
        timeLeftDisplayEl.textContent = `Time left: ${timeLeft}`;
        clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            timeLeft--;
            timeLeftDisplayEl.textContent = `Time left: ${timeLeft}`;
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                processAnswer(false); // Time ran out, process as unanswered/incorrect
            }
        }, 1000);
    }

    function displayQuestion() {
        showElements(true); // Show test area
        answerInputEl.value = '';
        answerInputEl.focus();

        if (currentQuestionSet === 'practice' && currentQuestionIndex >= NUM_PRACTICE_QUESTIONS) {
            // Finished practice, switch to main test
            currentQuestionSet = 'main';
            questions = mainQuestions;
            currentQuestionIndex = 0;
            if (questions.length === 0) { // Edge case: no main questions
                endTest();
                return;
            }
            displayMessage("Practice Complete! Get ready for the main test...", PAUSE_BETWEEN_QUESTIONS * 1000, displayQuestion);
            return;
        }

        if (currentQuestionIndex >= questions.length) {
            // Finished all questions in the current set (either practice or main)
            endTest();
            return;
        }

        const q = questions[currentQuestionIndex];
        questionTextEl.textContent = `${q.op1} × ${q.op2} =`;

        if (currentQuestionSet === 'practice') {
            questionCounterEl.textContent = `P${currentQuestionIndex + 1}/${NUM_PRACTICE_QUESTIONS}`;
        } else {
            questionCounterEl.textContent = `${currentQuestionIndex + 1}/${numTotalMainQuestions}`;
        }
        startTimer();
    }

    function processAnswer(submittedViaEnterOrKeypad = true) {
        clearInterval(timerInterval);
        const timeTakenMs = Date.now() - questionStartTime;
        const timeTakenSec = parseFloat((timeTakenMs / 1000).toFixed(1));

        const currentQ = questions[currentQuestionIndex];
        const userAnswer = answerInputEl.value.trim();
        
        let isCorrect = false;
        if (submittedViaEnterOrKeypad && userAnswer === String(currentQ.answer)) {
            isCorrect = true;
            if (currentQuestionSet === 'main') {
                score++;
            }
        }

        if (currentQuestionSet === 'main') {
            answeredQuestionsData.push({
                question: `${currentQ.op1}x${currentQ.op2}`,
                user_answer: userAnswer,
                correct_answer: currentQ.answer,
                is_correct: isCorrect,
                time_taken_seconds: timeTakenSec,
                timed_out: !submittedViaEnterOrKeypad && userAnswer === ''
            });
        }
        
        currentQuestionIndex++;
        timeLeftDisplayEl.textContent = "Next...";

        setTimeout(() => {
            // Check if we need to switch from practice to main or if test ends
            if (currentQuestionSet === 'practice' && currentQuestionIndex >= NUM_PRACTICE_QUESTIONS) {
                displayQuestion(); // Will trigger the switch to main test logic
            } else if (currentQuestionIndex < questions.length) {
                displayQuestion(); // Next question in current set
            } else {
                endTest(); // End of current set (and no next set)
            }
        }, PAUSE_BETWEEN_QUESTIONS * 1000);
    }

    async function endTest() {
        clearInterval(timerInterval);
        displayMessage("Test Complete! Submitting results...", 0); // Message stays until redirect or error
        timeLeftDisplayEl.textContent = "Finished";
        questionCounterEl.textContent = "Done";
        keypadBtns.forEach(btn => btn.disabled = true);
        answerInputEl.disabled = true;


        const payload = {
            score: score,
            total_questions: numTotalMainQuestions, // This should be length of mainQuestions
            answered_questions: answeredQuestionsData
        };

        try {
            const response = await fetch(submitUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json(); // Try to parse JSON regardless of response.ok

            if (response.ok && result.status === 'success' && result.attempt_id) {
                // SUCCESS CASE
                displayMessage("Results Submitted! Redirecting...", 2000, () => {
                    const finalTestCompleteUrl = testCompleteUrlTemplate.replace('PLACEHOLDER_ATTEMPT_ID', result.attempt_id);
                    window.location.href = finalTestCompleteUrl;
                });
            } else {
                // ERROR CASE (server responded, but not with success or missing data)
                let errorMessage = 'Could not submit results.';
                if (result && result.message) {
                    errorMessage = result.message;
                } else if (!response.ok) {
                    errorMessage = `Server error: ${response.statusText || response.status}`;
                }
                displayMessage(`Error: ${errorMessage}. Please inform your teacher.`, 10000, () => {
                    window.location.href = "/"; // Redirect to a safe page (e.g., student selection or home)
                });
            }
        } catch (error) {
            // CATCH BLOCK (Network error, or JSON parsing failed, etc.)
            displayMessage(`Network Error: ${error.message || 'Could not submit results.'}. Please check your connection and inform your teacher.`, 10000, () => {
                window.location.href = "/"; // Redirect to a safe page
            });
        }
    }

    keypadBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.disabled) return;
            const value = btn.dataset.value;
            if (value === 'C') {
                answerInputEl.value = '';
            } else if (value === 'Enter') {
                if (answerInputEl.value.trim() !== '') {
                    processAnswer(true);
                }
            } else {
                if (answerInputEl.value.length < 3) { // Max 3 digits for answer
                    answerInputEl.value += value;
                }
            }
            answerInputEl.focus();
        });
    });

    document.addEventListener('keydown', (event) => {
        // Only process keydown if keypad is visible (i.e., test is active)
        const keypadEl = document.querySelector('.keypad');
        if (!keypadEl || keypadEl.style.display === 'none' || answerInputEl.disabled) return;

        const key = event.key;
        if (key >= '0' && key <= '9') {
            event.preventDefault();
            if (answerInputEl.value.length < 3) {
                answerInputEl.value += key;
            }
        } else if (key === 'Backspace') {
            event.preventDefault();
            answerInputEl.value = answerInputEl.value.slice(0, -1);
        } else if (key === 'Enter') {
            event.preventDefault();
            if (answerInputEl.value.trim() !== '') {
                // Simulate click on Enter button to maintain single processing point
                const enterButton = document.getElementById('keypad-enter');
                if(enterButton) enterButton.click();
            }
        } else if (key.toLowerCase() === 'c') { // Allow 'c' or 'C' for clear
            event.preventDefault();
            const clearButton = document.getElementById('keypad-clear');
            if(clearButton) clearButton.click();
        }
        // No need to call answerInputEl.focus() here if it's already focused
        // and keypad clicks handle it.
    });
    
    // Initial message and start of the test (practice questions first)
    if (NUM_PRACTICE_QUESTIONS > 0) {
        displayMessage("Get Ready for Practice!", PAUSE_BETWEEN_QUESTIONS * 1000, displayQuestion);
    } else if (mainQuestions.length > 0) { // No practice, straight to main
        currentQuestionSet = 'main';
        questions = mainQuestions;
        displayMessage("Get Ready for the Test!", PAUSE_BETWEEN_QUESTIONS * 1000, displayQuestion);
    } else { // No questions at all
        displayMessage("No questions available for the test.", 0);
        timeLeftDisplayEl.textContent = "Error";
        questionCounterEl.textContent = "N/A";
    }
});