/* ============================================================
   Typing Tutor – Frontend (Final Version)
   ============================================================ */

class SimpleTypingApp {
    constructor() {
        /* ---------- Run-time state ---------- */
        this.currentText    = "";
        this.userInput      = "";
        this.startTime      = null;
        this.endTime        = null;
        this.isTestActive   = false;
        this.timer          = null;
        this.timeLimit      = 60;   // seconds
        this.errors         = 0;
        this.totalTyped     = 0;
        this.rawMistakes    = 0;
        this.backspaceCount = 0;
        this.lastFeedback   = "";

        /* ---------- Sentence Libraries ---------- */
        this.usedTexts = { beginner: [], intermediate: [], advanced: [] };

        this.textContent = {
            beginner: [
                "The cat sat on the mat and looked around the room.",
                "A dog ran in the park with his ball and toy.",
                "The sun is bright and the sky is blue today.",
                "I like to eat pizza and drink cold water.",
                "The bird flew over the tree, then landed near the bench."
            ],
            intermediate: [
                "Technology has revolutionized the way we communicate and work in modern society.",
                "Programming requires logical thinking and attention to detail for successful outcomes.",
                "The internet connects people from all around the world instantly and efficiently.",
                "Learning new skills takes practice, dedication, and consistent effort over time."
            ],
            advanced: [
                "Quantum computing represents a paradigm shift in computational capabilities.",
                "Machine learning algorithms can identify patterns in massive datasets impossible for humans to detect.",
                "Cybersecurity frameworks protect organizations from sophisticated threats while maintaining access.",
                "Artificial intelligence is transforming industries from healthcare to transportation."
            ]
        };

        /* ---------- Bootstrapping ---------- */
        this.bindEvents();
        this.generateNewText();   // First prompt
        this.updateDisplay();
    }

    /* ========== DOM Event Wiring ========== */
    bindEvents() {
        document.getElementById("startBtn")?.addEventListener("click", () => this.startTest());
        document.getElementById("resetBtn")?.addEventListener("click", () => this.resetTest());
        document.getElementById("newTestBtn")?.addEventListener("click", () => this.newTest());
        document.getElementById("difficulty")?.addEventListener("change", () => this.generateNewText());

        document.getElementById("closeLevelModalBtn")?.addEventListener("click", () => this.closeLevelModal());
        document.getElementById("closeFeedbackModalBtn")?.addEventListener("click", () => this.closeFeedbackModal());

        const input = document.getElementById("typingInput");
        if (input) {
            input.addEventListener("input",  e => this.handleTyping(e));
            input.addEventListener("keydown",e => this.handleKeyDown(e));
            input.disabled = true; 
        }
    }

    /* ========== Sentence Selection ========== */
    generateNewText() {
        const diffEl = document.getElementById("difficulty");
        if (!diffEl) return;
        
        const diff   = diffEl.value;
        const pool   = this.textContent[diff];
        let   used   = this.usedTexts[diff];

        let remain   = pool.filter(t => !used.includes(t));
        if (remain.length === 0) { used = []; remain = [...pool]; }

        const sentence = remain[Math.floor(Math.random()*remain.length)];

        this.currentText = sentence;
        used.push(sentence);
        this.usedTexts[diff] = used;

        const textContent = document.getElementById("textContent");
        const typingInput = document.getElementById("typingInput");
        
        if (textContent) textContent.textContent = this.currentText;
        if (typingInput) typingInput.value = "";
        
        this.userInput = "";
        this.updateTextDisplay();
    }

    /* ========== Test Lifecycle ========== */
    startTest() {
        if (this.isTestActive) return;

        this.errors = this.totalTyped = this.rawMistakes = this.backspaceCount = 0;
        this.startTime     = new Date();
        this.isTestActive  = true;

        const input = document.getElementById("typingInput");
        input.disabled = false;
        input.focus();

        const btn = document.getElementById("startBtn");
        if (btn) {
            btn.textContent = "Test in Progress...";
            btn.disabled    = true;
        }
        
        const timerDisplay = document.getElementById("timerDisplay");
        if (timerDisplay) timerDisplay.style.display = "block";

        this.startTimer();
    }

    startTimer() {
        let left = this.timeLimit;
        this.updateTimerDisplay(left);

        this.timer = setInterval(() => {
            left--;
            this.updateTimerDisplay(left);
            if (left <= 0) { clearInterval(this.timer); this.endTest(); }
        }, 1000);
    }

    updateTimerDisplay(sec){
        const el = document.getElementById("timerText");
        if (el) el.textContent = `${Math.floor(sec/60)}:${(sec%60).toString().padStart(2,"0")}`;
    }

    /* ---------- Keystroke Handling ---------- */
    handleTyping(e) {
        if (!this.isTestActive) return;

        const prev = this.userInput;
        this.userInput = e.target.value;
        const idx = this.userInput.length-1;

        if (this.userInput.length > prev.length &&
            this.userInput[idx] !== this.currentText[idx]) {
            this.rawMistakes++;
        }

        this.totalTyped = this.userInput.length;
        this.calculateErrors();
        this.updateTextDisplay();
        this.updateLiveMetrics();

        if (this.userInput.length >= this.currentText.length) this.endTest();
    }

    handleKeyDown(e){ 
        if(e.key === "Backspace" && this.isTestActive) this.backspaceCount++; 
    }

    calculateErrors(){
        this.errors = 0;
        for (let i=0; i<this.userInput.length; i++) {
            if (this.userInput[i] !== this.currentText[i]) this.errors++;
        }
    }

    /* ---------- Visuals ---------- */
    updateTextDisplay(){
        const el = document.getElementById("textContent");
        if (!el) return;

        let html = "";
        for (let i=0; i<this.currentText.length; i++){
            const ch = this.currentText[i];
            if (i < this.userInput.length) {
                 const isCorrect = this.userInput[i] === ch;
                 html += `<span class="${isCorrect ? 'correct' : 'incorrect'}">${ch}</span>`;
            } else if (i === this.userInput.length) {
                 html += `<span class="current">${ch}</span>`;
            } else {
                 html += ch;
            }
        }
        el.innerHTML = html;
    }

    updateLiveMetrics(){
        const mins = (new Date()-this.startTime)/60000 || 1;
        const wpm  = Math.round((this.totalTyped/5)/mins);
        const acc  = this.totalTyped ? Math.round(((this.totalTyped-this.errors)/this.totalTyped)*100) : 100;
        
        const wpmEl = document.getElementById("displayWPM");
        const accEl = document.getElementById("displayAccuracy");
        const scoreEl = document.getElementById("displayScore");

        if (wpmEl) wpmEl.textContent = wpm;
        if (accEl) accEl.textContent = `${acc}%`;
        if (scoreEl) scoreEl.textContent = Math.round(wpm*(acc/100));
    }

    /* ========== Finishing & Backend Call ========== */
    endTest(){
        if (!this.isTestActive) return;
        this.isTestActive = false;
        clearInterval(this.timer);

        document.getElementById("typingInput").disabled = true;
        const btn = document.getElementById("startBtn");
        if (btn) {
            btn.textContent = "Start Test"; 
            btn.disabled = false;
        }
        document.getElementById("timerDisplay").style.display = "none";

        /* ---- Send to Backend /analyze ---- */
        const secs = (new Date()-this.startTime)/1000;
        
        const payload = {
            wpm:         (this.totalTyped/5)/(secs/60),
            accuracy:    this.totalTyped ? ((this.totalTyped-this.errors)/this.totalTyped)*100 : 100,
            error_count: this.errors,
            raw_mistakes: this.rawMistakes,
            backspace_count: this.backspaceCount, 
            time_taken:  secs,
            typed_text:  this.userInput,
            target_text: this.currentText
        };

        fetch("https://smart-typing-tutor.onrender.com/analyze", {
            method: "POST",
            headers: { "Content-Type":"application/json" },
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(data => {
            this.lastFeedback = data.feedback || "Keep practising!";
            
            this.showLevelModal(data.level || "Intermediate");
            this.calculateResults(data.level || "Intermediate");
            this.displayAIRecommendation(this.lastFeedback);

           saveSessionToBackend({
             ...payload,
             level: data.level || "Unknown"
           });
        })
        .catch(err => {
            console.error("Analyze error:", err);
            this.lastFeedback = "- ⚠️ Backend not running. Run app.py!";
            this.displayAIRecommendation(this.lastFeedback);
        });
    }

    /* ---------- Modals & Feedback ---------- */
    showLevelModal(level){
        const modal = document.getElementById("levelModal");
        const msg = document.getElementById("levelMessage");
        if (modal && msg) {
            msg.textContent = `🎉 You are a ${level}`;
            modal.style.display = "flex";
        }
    }
    
    closeLevelModal(){ 
        const modal = document.getElementById("levelModal");
        if (modal) modal.style.display="none"; 
    }

    closeFeedbackModal(){ 
        const modal = document.getElementById("feedbackModal");
        if (modal) modal.style.display="none"; 
    }

    displayAIRecommendation(text){
        const list = document.getElementById("recommendationList");
        if (!list) return;

        list.innerHTML = ""; 

        // Split by lines and clean bullets
        text.split(/\n+/).forEach(line => {
            const cleanLine = line.trim();
            if (!cleanLine) return;
            const finalLine = cleanLine.replace(/^[-*•]\s*/, ""); // Removes Markdown bullets
            
            const div = document.createElement("div");
            div.className = "recommendation-item";
            div.textContent = `🤖 ${finalLine}`;
            list.appendChild(div);
        });
    }

    /* ---------- Results Display ---------- */
    calculateResults(level){
        const secs = (this.endTime ? this.endTime : new Date()) - this.startTime;
        const mins = secs/60000;
        const wpm  = Math.round((this.totalTyped/5)/mins);
        const acc  = this.totalTyped ? Math.round(((this.totalTyped-this.errors)/this.totalTyped)*100) : 100;

        document.getElementById("resultTimeTaken").textContent = this.formatTime(secs/1000);
        document.getElementById("resultWPM").textContent       = wpm;
        document.getElementById("resultAccuracy").textContent  = `${acc}%`;
        document.getElementById("resultErrors").textContent    = this.errors;
        document.getElementById("resultLevel").textContent     = level;
        document.getElementById("resultRawMistakes").textContent = this.rawMistakes;
        document.getElementById("resultBackspaces").textContent  = this.backspaceCount;

        const resultsSec = document.getElementById("resultsSection");
        if (resultsSec) resultsSec.style.display = "block";
    }

    /* ---------- Misc ---------- */
    resetTest(){ location.reload(); }
    
    newTest()  { 
        this.generateNewText(); 
        this.errors = this.totalTyped = this.rawMistakes = this.backspaceCount = 0;
        this.isTestActive = false;
        clearInterval(this.timer);
        
        const input = document.getElementById("typingInput");
        if(input) {
            input.value = "";
            input.disabled = false;
        }
        
        const btn = document.getElementById("startBtn");
        if(btn) {
            btn.textContent = "Start Test"; 
            btn.disabled = false;
        }
        
        this.updateDisplay();
    }

    updateDisplay(){
        const wpmEl = document.getElementById("displayWPM");
        if (wpmEl) wpmEl.textContent = "0";
        document.getElementById("displayAccuracy").textContent = "100%";
        document.getElementById("displayScore").textContent    = "0";
    }
    
    formatTime(s){ return `${Math.floor(s/60)}:${(Math.floor(s)%60).toString().padStart(2,"0")}`; }
}

/* ---------- SAVE SESSION HELPER ---------- */
function saveSessionToBackend(payload) {
  const token = localStorage.getItem("quickeys_token");
  if (!token) return; 

  fetch("https://smart-typing-tutor.onrender.com/session", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  }).catch(err => console.warn("Could not save session:", err));
}

/* ---------- Bootstrap ---------- */
document.addEventListener("DOMContentLoaded",()=>{ window.app = new SimpleTypingApp(); });