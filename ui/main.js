
console.log('[AlgoTrainer] main.js loaded');


window.MonacoEnvironment = {
    getWorkerUrl: function (workerId, label) {
        return 'vs/editor/editor.worker.js';
    }
};


async function copyCodeToClipboard() {
    if (!editor) return;
    const code = editor.getValue();
    try {
        await navigator.clipboard.writeText(code);
        const copyBtn = document.getElementById('copy-btn');
        if (copyBtn) {
            const originalText = copyBtn.innerText;
            copyBtn.innerText = '✅ Copied!';
            setTimeout(() => { copyBtn.innerText = originalText; }, 2000);
        }
    } catch (err) {
        console.error('Failed to copy: ', err);
    }
}


function startTimer() {
  stopTimer();
  timerSeconds = 600;
  timerRunning = true;
  updateTimerDisplay();

  timerInterval = setInterval(function() {
    timerSeconds--;
    updateTimerDisplay();

    if (timerSeconds <= 0) {
      stopTimer();
      timerElement.classList.add('critical');
      showTimeUpModal();
    } else if (timerSeconds <= 60) {

      timerElement.classList.add('critical');
    }
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  timerRunning = false;
}

function updateTimerDisplay() {
  const minutes = Math.floor(timerSeconds / 60);
  const seconds = timerSeconds % 60;
  timerElement.textContent =
    String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');
}


function showTimeUpModal() {
  const modal = document.getElementById('time-up-modal');
  const messageEl = document.getElementById('time-up-message');
  const closeBtn = document.getElementById('time-up-close-btn');
  const modalTitle = document.getElementById('modal-title');


  const randomPhrase = TIME_UP_PHRASES[Math.floor(Math.random() * TIME_UP_PHRASES.length)];
  messageEl.textContent = randomPhrase;


  closeBtn.textContent = 'Exit';


  modal.style.display = 'flex';


  if (editor) {
    editor.updateOptions({ readOnly: true });
  }
  const runBtn = document.getElementById('run-btn');
  if (runBtn) {
    runBtn.disabled = true;
    runBtn.textContent = 'Time\'s Up';
  }


  const closeModal = function() {

    if (currentProblem && currentProblem.id) {
      localStorage.removeItem(`code_problem_${currentProblem.id}`);
    }


    if (editor) {
      editor.setValue('');
      editor.updateOptions({ readOnly: false });
    }


    const runBtn = document.getElementById('run-btn');
    if (runBtn) {
      runBtn.disabled = false;
      runBtn.textContent = 'Run Code (Ctrl+Enter)';
    }


    modal.style.display = 'none';
    workspaceView.style.display = 'none';
    problemListView.style.display = 'flex';


    const header = document.getElementById('main-header');
    if (header) header.style.display = 'flex';

    currentProblem = null;
    testResults.style.display = 'none';
    stopTimer();


    document.removeEventListener('keydown', handleEnterKey);
    closeBtn.removeEventListener('click', closeModal);
    modal.querySelector('.modal-overlay').removeEventListener('click', closeModal);
  };


  const handleEnterKey = function(e) {
    if (e.key === 'Enter') {
      closeModal();
    }
  };


  document.addEventListener('keydown', handleEnterKey);
  closeBtn.addEventListener('click', closeModal);
  modal.querySelector('.modal-overlay').addEventListener('click', closeModal);
}


function initResizable() {
  const resizeHandle = document.getElementById('resize-handle');
  const problemDescription = document.getElementById('problem-description');
  const editorSection = document.getElementById('editor-section');

  if (!resizeHandle || !problemDescription || !editorSection) return;

  let isResizing = false;

  resizeHandle.addEventListener('mousedown', function(e) {
    isResizing = true;
    resizeHandle.classList.add('resizing');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  });

  document.addEventListener('mousemove', function(e) {
    if (!isResizing) return;

    const containerWidth = document.querySelector('.workspace-container').offsetWidth;
    const newWidth = e.clientX;


    if (newWidth >= 250 && newWidth <= 600) {
      problemDescription.style.width = newWidth + 'px';
      if (editor) {
        editor.layout();
      }
    }
  });

  document.addEventListener('mouseup', function() {
    if (isResizing) {
      isResizing = false;
      resizeHandle.classList.remove('resizing');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  });
}


window.copyCodeToClipboard = copyCodeToClipboard;
window.resetCodeToTemplate = resetCodeToTemplate;


let editor = null;
let currentProblem = null;
let problems = [];


let timerInterval = null;
let timerSeconds = 600;
let timerRunning = false;


let problemSolved = false;


let solvedProblemsSet = new Set();


const TIME_UP_PHRASES = [
  "Don't give up! Every great programmer started where you are now.",
  "Practice makes perfect! Try again, you'll get it next time.",
  "The journey of a thousand miles begins with a single step.",
  "Coding is a skill that grows with every challenge you face.",
  "Take a break, refresh your mind, and come back stronger!",
  "Every bug you fix makes you a better developer.",
  "The best way to learn is by doing. Keep coding!",
  "Remember: even the experts started with 'Hello, World!'",
  "Progress, not perfection. You're getting better every day!",
  "Challenges are opportunities in disguise. Embrace them!",
];


let editorReady = false;
let pywebviewReady = false;


const problemListView = document.getElementById('problem-list-view');
const taskListScroll = document.getElementById('task-list-scroll');
const searchInput = document.getElementById('search-input');
const loadingMsg = document.getElementById('loading-msg');
const errorMsg = document.getElementById('error-msg');
const statEasy = document.getElementById('stat-easy');
const statMedium = document.getElementById('stat-medium');
const statHard = document.getElementById('stat-hard');
const statTotalSubmissions = document.getElementById('stat-total-submissions');
const statProblemsSolved = document.getElementById('stat-problems-solved');
const statTimeSpent = document.getElementById('stat-time-spent');
const resetStatsBtn = document.getElementById('reset-stats-btn');


const sortBtn = document.getElementById('sort-btn');
const sortDropdown = document.getElementById('sort-dropdown');
const filterBtn = document.getElementById('filter-btn');
const filterDropdown = document.getElementById('filter-dropdown');
const randomBtn = document.getElementById('random-btn');


let currentSort = 'default';
let currentFilter = 'all';


const workspaceView = document.getElementById('workspace-view');
const backBtn = document.getElementById('back-btn');
const problemTitle = document.getElementById('problem-title');
const problemAccent = document.getElementById('problem-accent');
const problemCondition = document.getElementById('problem-condition');
const authorSolutionBtn = document.getElementById('author-solution-btn');
const runBtn = document.getElementById('run-btn');
const testResults = document.getElementById('test-results');
const resultsSummary = document.getElementById('results-summary');
const testResultsList = document.getElementById('test-results-list');
const timerElement = document.getElementById('timer');


require.config({ paths: { vs: 'vs' } });

require(['vs/editor/editor.main'], function () {
  console.log('[AlgoTrainer] Monaco require callback fired');
  try {

    editor = monaco.editor.create(document.getElementById('monaco-editor'), {
      ...EDITOR_CONFIG,
      theme: 'vs-dark',
      value: '',
    });


    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
      function () {
        runTests();
      }
    );





    const blockedKeybindings = [
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyG,
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyI,
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.Space,
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyQ,
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyJ,
      monaco.KeyCode.F1,
    ];

    blockedKeybindings.forEach(kb => {
      editor.addCommand(kb, function() {

        return false;
      });
    });

    console.log('[AlgoTrainer] Keybindings blocked (Tab still works)');

    console.log('[AlgoTrainer] Setting editorReady = true');
    editorReady = true;


    initResizable();

    tryInit();
  } catch (err) {
    console.error('[AlgoTrainer] Monaco init failed:', err);

    editorReady = true;
    tryInit();
  }
}, function (err) {

  console.error('[AlgoTrainer] Failed to load Monaco:', err);
  editorReady = true;
  tryInit();
});


async function initApp() {
    console.log('[AlgoTrainer] initApp called');
    try {

        let apiReady = false;
        let attempts = 0;
        const maxAttempts = 50;
        const retryDelay = 100;

        while (!apiReady && attempts < maxAttempts) {
            try {
                if (pywebview.api && typeof pywebview.api.get_problems === 'function') {
                    apiReady = true;
                    console.log('[AlgoTrainer] API ready after ' + (attempts * retryDelay) + 'ms');
                } else {
                    attempts++;
                    await new Promise(resolve => setTimeout(resolve, retryDelay));
                }
            } catch (e) {
                attempts++;
                await new Promise(resolve => setTimeout(resolve, retryDelay));
            }
        }

        if (!apiReady) {
            throw new Error('pywebview.api.get_problems not ready after ' + (maxAttempts * retryDelay) + 'ms');
        }

        await init();
    } catch (error) {
        console.error('[AlgoTrainer] Initialization failed:', error);
        showError('Failed to connect to Python backend: ' + error.message);
    }
}


function tryInit() {
    console.log('[AlgoTrainer] tryInit called, editorReady=' + editorReady + ' pywebviewReady=' + pywebviewReady);
    if (editorReady && pywebviewReady) {
        initApp();
    }
}


function tryInit() {
    console.log('[AlgoTrainer] tryInit called, editorReady=' + editorReady + ' pywebviewReady=' + pywebviewReady);
    if (editorReady && pywebviewReady) {
        initApp();
    }
}


function initSolvedProblemsCache() {
  solvedProblemsSet.clear();
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith('solved_problem_')) {
      try {
        const solvedData = JSON.parse(localStorage.getItem(key));
        if (solvedData && solvedData.problemId) {
          const problemId = parseInt(solvedData.problemId, 10);
          if (!isNaN(problemId)) {
            solvedProblemsSet.add(problemId);
          }
        }
      } catch (e) {
        console.error('[initSolvedProblemsCache] Error parsing solved data:', e);
      }
    }
  }
  console.log('[AlgoTrainer] Solved problems cache initialized:', solvedProblemsSet.size, 'problems');
}


async function init() {
  console.log('[AlgoTrainer] init() called');
  try {

    const cached = localStorage.getItem('problem_summaries');
    const cachedTimestamp = localStorage.getItem('problem_summaries_timestamp');
    const now = Date.now();
    const ONE_HOUR_MS = 60 * 60 * 1000;

    if (cached && cachedTimestamp && (now - parseInt(cachedTimestamp)) < ONE_HOUR_MS) {

      problems = JSON.parse(cached);
      console.log('[AlgoTrainer] problems loaded from cache:', problems.length);

      initSolvedProblemsCache();
      renderProblemList();
    } else {

      const response = await pywebview.api.get_problems();

      if (response.error) {
        showError(response.error);
        return;
      }

      problems = response.problems || [];
      console.log('[AlgoTrainer] problems loaded from backend:', problems.length);


      localStorage.setItem('problem_summaries', JSON.stringify(problems));
      localStorage.setItem('problem_summaries_timestamp', now.toString());


      initSolvedProblemsCache();
      updateSolvedProblemsList();


      loadStatistics();

      renderProblemList();
    }
  } catch (err) {
    console.error('[AlgoTrainer] init error:', err);
    showError('Failed to load problems: ' + err.message);
  }
}


function renderProblemList() {
  loadingMsg.style.display = 'none';

  if (problems.length === 0) {
    taskListScroll.innerHTML = '<div class="loading">No problems available</div>';
    return;
  }





  let filtered = problems.filter(p => {

    const searchQuery = searchInput.value.toLowerCase();
    if (searchQuery && !p.title.toLowerCase().includes(searchQuery)) {
      return false;
    }


    const statusFilters = Array.from(document.querySelectorAll('input[name="filter-status"]:checked')).map(cb => cb.value);
    const diffFilters = Array.from(document.querySelectorAll('input[name="filter-diff"]:checked')).map(cb => cb.value);
    const specialFilters = Array.from(document.querySelectorAll('input[name="filter"]:checked')).map(cb => cb.value);


    if (statusFilters.length > 0) {
      const isSolved = solvedProblemsSet.has(Number(p.id));


      const bothChecked = statusFilters.includes('solved') && statusFilters.includes('unsolved');
      if (bothChecked) {

      } else if (statusFilters.includes('solved') && !isSolved) {
        return false;
      } else if (statusFilters.includes('unsolved') && isSolved) {
        return false;
      }
    }


    if (diffFilters.length > 0) {
      const diffLower = p.difficulty.toLowerCase();
      if (!diffFilters.includes(diffLower)) return false;
    }


    if (specialFilters.includes('yandex') && !p.title.toLowerCase().includes('yandex')) {
      return false;
    }

    return true;
  });


  if (currentSort === 'difficulty') {
    const diffOrder = { 'Easy': 1, 'Medium': 2, 'Hard': 3 };
    filtered.sort((a, b) => diffOrder[a.difficulty] - diffOrder[b.difficulty] || a.id - b.id);
  } else if (currentSort === 'difficulty-desc') {
    const diffOrder = { 'Easy': 1, 'Medium': 2, 'Hard': 3 };
    filtered.sort((a, b) => diffOrder[b.difficulty] - diffOrder[a.difficulty] || a.id - b.id);
  } else if (currentSort === 'title') {
    filtered.sort((a, b) => a.title.localeCompare(b.title));
  }


  taskListScroll.innerHTML = filtered.map((p, index) => {
    const diffClass = p.difficulty.toLowerCase();
    const isSolved = solvedProblemsSet.has(Number(p.id));
    return `
      <div class="task-row ${isSolved ? 'solved' : ''}" data-id="${p.id}">
        <div class="task-accent ${diffClass}"></div>
        <div class="task-content">
          <span class="task-number">${p.id}.</span>
          <span class="task-title">${p.title}${isSolved ? ' ✅' : ''}</span>
          <span class="task-difficulty ${diffClass}">${p.difficulty}</span>
        </div>
      </div>
    `;
  }).join('');


  document.querySelectorAll('.task-row').forEach(row => {
    row.addEventListener('click', () => {
      const id = parseInt(row.dataset.id);
      openProblem(id);
    });
  });
}


function showError(message) {
  loadingMsg.style.display = 'none';
  errorMsg.textContent = message;
  errorMsg.style.display = 'block';
}


function goBack() {

  if (problemSolved && currentProblem && currentProblem.id) {
    localStorage.removeItem(`code_problem_${currentProblem.id}`);
  }

  workspaceView.style.display = 'none';
  problemListView.style.display = 'flex';
  currentProblem = null;
  testResults.style.display = 'none';


  stopTimer();


  const header = document.getElementById('main-header');
  if (header) header.style.display = 'flex';
}


async function openProblem(id) {
  try {
    const response = await pywebview.api.get_problem(id);

    if (response.error) {
      alert(response.error);
      return;
    }

    currentProblem = response.problem;


    await pywebview.api.start_problem_session(currentProblem.id);


    problemSolved = false;


    problemTitle.textContent = currentProblem.title;


    const diffClass = currentProblem.difficulty.toLowerCase();
    problemAccent.className = `problem-accent ${diffClass}`;


    problemCondition.innerHTML = currentProblem.condition || '<p>No description available</p>';


    console.log('[AuthorSolution] openProblem:', currentProblem.id, currentProblem.title);
    console.log('[AuthorSolution] author_solution:', currentProblem.author_solution ? 'EXISTS (' + currentProblem.author_solution.length + ' chars)' : 'MISSING');

    if (authorSolutionBtn) {
      if (currentProblem.author_solution && currentProblem.author_solution.trim() !== '') {
        authorSolutionBtn.disabled = false;
        authorSolutionBtn.classList.remove('disabled');
        console.log('[AuthorSolution] Button ENABLED');
      } else {
        authorSolutionBtn.disabled = true;
        authorSolutionBtn.classList.add('disabled');
        console.log('[AuthorSolution] Button DISABLED');
      }
    }


    if (editor) {

      const savedCode = localStorage.getItem(`code_problem_${currentProblem.id}`);
      const codeToLoad = savedCode || (currentProblem.template || '');
      editor.setValue(codeToLoad);


      if (!editor._saveHandlerAttached) {
        editor.onDidChangeModelContent(() => {
          if (currentProblem && currentProblem.id) {
            const code = editor.getValue();
            localStorage.setItem(`code_problem_${currentProblem.id}`, code);
          }
        });
        editor._saveHandlerAttached = true;
      }



      const model = editor.getModel();
      const lineCount = model.getLineCount();

      let targetLine = lineCount;
      for (let i = lineCount; i >= 1; i--) {
        const content = model.getLineContent(i);
        if (content.trim() === '' && content.length > 0) {

          targetLine = i;
          break;
        }
      }

      const targetCol = model.getLineContent(targetLine).length + 1;
      editor.setPosition({ lineNumber: targetLine, column: targetCol });
      editor.revealLineInCenter(targetLine);
    }


    testResults.style.display = 'none';


    problemListView.style.display = 'none';
    workspaceView.style.display = 'flex';


    const header = document.getElementById('main-header');
    if (header) header.style.display = 'none';


    timerElement.classList.remove('critical');
    startTimer();


    if (editor) {

      requestAnimationFrame(function () {
        editor.layout();
        editor.focus();
      });
    }

  } catch (err) {
    alert('Failed to load problem: ' + err.message);
  }
}


if (searchInput) {
  searchInput.addEventListener('input', function() {
    renderProblemList();
  });
}


function toggleDropdown(dropdown) {
  const allDropdowns = document.querySelectorAll('.dropdown-menu');
  allDropdowns.forEach(d => {
    if (d !== dropdown) d.classList.remove('show');
  });
  dropdown.classList.toggle('show');
}


document.addEventListener('click', function(e) {
  if (!e.target.closest('.dropdown-container')) {
    document.querySelectorAll('.dropdown-menu').forEach(d => d.classList.remove('show'));
  }
});


if (sortBtn && sortDropdown) {
  sortBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleDropdown(sortDropdown);
  });

  sortDropdown.querySelectorAll('.dropdown-item').forEach(item => {
    item.addEventListener('click', function() {
      currentSort = this.dataset.sort;


      sortDropdown.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('active'));
      this.classList.add('active');

      renderProblemList();
      sortDropdown.classList.remove('show');
    });
  });
}


if (filterBtn && filterDropdown) {
  filterBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleDropdown(filterDropdown);
  });


  filterDropdown.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      renderProblemList();
      updateFilterButtonCount();
    });
  });


  const clearBtn = document.getElementById('filter-clear-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', function() {
      filterDropdown.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
      });
      renderProblemList();
      updateFilterButtonCount();
      filterDropdown.classList.remove('show');
    });
  }
}


function updateFilterButtonCount() {
  const checkedCount = filterDropdown.querySelectorAll('input[type="checkbox"]:checked').length;
  const btnText = filterBtn.querySelector('.btn-text');

  if (checkedCount === 0) {
    btnText.textContent = 'Filter';
  } else {
    btnText.textContent = `Filter (${checkedCount})`;
  }
}


if (randomBtn) {
  randomBtn.addEventListener('click', function() {



    let filtered = problems.filter(p => {

      const searchQuery = searchInput.value.toLowerCase();
      if (searchQuery && !p.title.toLowerCase().includes(searchQuery)) {
        return false;
      }


      const statusFilters = Array.from(document.querySelectorAll('input[name="filter-status"]:checked')).map(cb => cb.value);
      const diffFilters = Array.from(document.querySelectorAll('input[name="filter-diff"]:checked')).map(cb => cb.value);
      const specialFilters = Array.from(document.querySelectorAll('input[name="filter"]:checked')).map(cb => cb.value);


      if (statusFilters.length > 0) {
        const isSolved = solvedProblemsSet.has(p.id);
        if (statusFilters.includes('solved') && !isSolved) return false;
        if (statusFilters.includes('unsolved') && isSolved) return false;
      }


      if (diffFilters.length > 0) {
        const diffLower = p.difficulty.toLowerCase();
        if (!diffFilters.includes(diffLower)) return false;
      }


      if (specialFilters.includes('yandex') && !p.title.toLowerCase().includes('yandex')) {
        return false;
      }

      return true;
    });

    if (filtered.length === 0) {
      alert('No problems available with current filters!');
      return;
    }


    const randomProblem = filtered[Math.floor(Math.random() * filtered.length)];
    openProblem(randomProblem.id);
  });
}


async function runTests() {
  if (!currentProblem || !editor) {
    return;
  }

  const code = editor.getValue();
  runBtn.disabled = true;
  runBtn.textContent = 'Running...';

  try {
    const response = await pywebview.api.run_tests(currentProblem.id, code);
    displayTestResults(response);


    if (response.results && response.results.length > 0) {
      const passedCount = response.results.filter(r => r.passed).length;
      const totalCount = response.results.length;


      await pywebview.api.record_submission(
        currentProblem.id,
        passedCount,
        totalCount,
        code
      );
    }


    if (response.success && response.results && response.results.length > 0) {
      const allPassed = response.results.every(r => r.passed);
      if (allPassed) {
        stopTimer();
        saveSolvedProblem(currentProblem.id, code, timerSeconds);
      }
    }
  } catch (err) {
    displayTestResults({
      success: false,
      error: 'Failed to run tests: ' + err.message,
      summary: 'Execution failed',
    });
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = 'Run Tests (Ctrl+Enter)';
  }
}


function saveSolvedProblem(problemId, code, timeRemaining) {
  const solvedKey = `solved_problem_${problemId}`;
  const timeSpent = 600 - timeRemaining;

  const solvedData = {
    problemId: problemId,
    problemTitle: currentProblem.title,
    difficulty: currentProblem.difficulty,
    code: code,
    timeSpent: timeSpent,
    timestamp: Date.now()
  };

  localStorage.setItem(solvedKey, JSON.stringify(solvedData));


  solvedProblemsSet.add(Number(problemId));


  problemSolved = true;


  updateSolvedProblemsList();


  renderProblemList();
}


function updateSolvedProblemsList() {
  const solvedList = document.getElementById('solved-problems-list');
  if (!solvedList) return;

  const solved = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith('solved_problem_')) {
      try {
        const data = JSON.parse(localStorage.getItem(key));
        solved.push(data);
      } catch (e) {}
    }
  }


  solved.sort((a, b) => b.timestamp - a.timestamp);

  if (solved.length === 0) {
    solvedList.innerHTML = '<div class="loading">No solved problems yet</div>';
  } else {
    solvedList.innerHTML = solved.map(s => {
      const minutes = Math.floor(s.timeSpent / 60);
      const seconds = s.timeSpent % 60;
      const timeStr = `${minutes}:${String(seconds).padStart(2, '0')}`;
      const diffClass = s.difficulty.toLowerCase();
      return `
        <div class="solved-problem-item" data-id="${s.problemId}">
          <div class="solved-problem-title">${s.problemTitle}</div>
          <div class="solved-problem-meta">
            <span class="solved-problem-difficulty ${diffClass}">${s.difficulty}</span>
            <span class="solved-problem-time">⏱ ${timeStr}</span>
          </div>
        </div>
      `;
    }).join('');


    solvedList.querySelectorAll('.solved-problem-item').forEach(item => {
      item.addEventListener('click', () => {
        const id = parseInt(item.dataset.id);
        openProblem(id);
      });
    });
  }


  updateStats(solved);
}


function updateStats(solved) {
  const easyCount = solved.filter(s => s.difficulty === 'Easy').length;
  const mediumCount = solved.filter(s => s.difficulty === 'Medium').length;
  const hardCount = solved.filter(s => s.difficulty === 'Hard').length;

  if (statEasy) statEasy.textContent = easyCount;
  if (statMedium) statMedium.textContent = mediumCount;
  if (statHard) statHard.textContent = hardCount;


  loadStatistics();
}


async function loadStatistics() {
  try {
    const stats = await pywebview.api.get_statistics();

    if (statTotalSubmissions) {
      statTotalSubmissions.textContent = stats.total_submissions || 0;
    }
    if (statProblemsSolved) {
      statProblemsSolved.textContent = stats.problems_solved || 0;
    }
    if (statTimeSpent) {
      const totalSeconds = stats.total_time_spent_seconds || 0;
      const minutes = Math.floor(totalSeconds / 60);
      const hours = Math.floor(minutes / 60);

      if (hours > 0) {
        statTimeSpent.textContent = `${hours}h ${minutes % 60}m`;
      } else {
        statTimeSpent.textContent = `${minutes}m`;
      }
    }
  } catch (err) {
    console.error('[Statistics] Failed to load:', err);
  }
}


function showResetStatisticsModal() {
  const modal = document.getElementById('reset-stats-modal');
  const modalOverlay = modal.querySelector('.modal-overlay');
  const cancelBtn = document.getElementById('reset-stats-cancel-btn');
  const confirmBtn = document.getElementById('reset-stats-confirm-btn');


  modal.style.display = 'flex';


  const handleResetConfirm = async function() {
    try {
      const result = await pywebview.api.reset_statistics();
      if (result.success) {

        loadStatistics();

        updateSolvedProblemsList();
        console.log('[Statistics] Reset successfully');
      }
    } catch (err) {
      console.error('[Statistics] Reset failed:', err);
    } finally {

      modal.style.display = 'none';
      cleanup();
    }
  };


  const handleResetCancel = function() {
    modal.style.display = 'none';
    cleanup();
  };


  const cleanup = function() {
    modalOverlay.removeEventListener('click', handleResetCancel);
    cancelBtn.removeEventListener('click', handleResetCancel);
    confirmBtn.removeEventListener('click', handleResetConfirm);
  };


  modalOverlay.addEventListener('click', handleResetCancel);
  cancelBtn.addEventListener('click', handleResetCancel);
  confirmBtn.addEventListener('click', handleResetConfirm);
}


function displayTestResults(results) {
  testResults.style.display = 'block';
  resultsSummary.textContent = results.summary || '';

  if (results.error) {
    testResultsList.innerHTML = `
      <div class="test-result test-error">
        <div class="test-header">
          <span class="test-icon">❌</span>
          <span class="test-status">Execution Error</span>
        </div>
        <div class="test-details">
          <pre class="error-message">${escapeHtml(results.error)}</pre>
        </div>
      </div>
    `;
    return;
  }

  const resultsHtml = (results.results || []).map(r => {
    if (r.passed) {
      return `
        <div class="test-result test-passed">
          <div class="test-header">
            <span class="test-icon">✅</span>
            <span class="test-status">Test ${r.test_num}: Passed</span>
          </div>
          ${r.stdout ? `<pre class="test-stdout">${escapeHtml(r.stdout)}</pre>` : ''}
        </div>
      `;
    } else {
      return `
        <div class="test-result test-failed">
          <div class="test-header">
            <span class="test-icon">❌</span>
            <span class="test-status">Test ${r.test_num}: Failed</span>
          </div>
          <div class="test-details">
            ${r.error ? `
              <div class="error-block">
                <strong>Error:</strong>
                <pre class="error-message">${escapeHtml(r.error)}</pre>
              </div>
            ` : `
              <div class="detail-row">
                <strong>Input:</strong> ${formatArgs(r.args)}
              </div>
              <div class="detail-row">
                <strong>Expected:</strong> <code>${escapeHtml(JSON.stringify(r.expected))}</code>
              </div>
              <div class="detail-row">
                <strong>Got:</strong> <code>${escapeHtml(JSON.stringify(r.got))}</code>
              </div>
            `}
            ${r.stdout ? `<pre class="test-stdout"><strong>Output:</strong>\n${escapeHtml(r.stdout)}</pre>` : ''}
          </div>
        </div>
      `;
    }
  }).join('');

  testResultsList.innerHTML = resultsHtml;
}


function showAuthorSolutionConfirmation(solution) {

  const modal = document.createElement('div');
  modal.id = 'author-solution-confirm-modal';
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-overlay"></div>
    <div class="modal-content author-solution-confirm-content">
      <div class="modal-header">
        <h3>⚠️ Заменить код?</h3>
      </div>
      <div class="modal-body">
        <p>Ваш текущий код будет <strong>полностью заменён</strong> на авторское решение.</p>
        <p class="warning-text">Это действие нельзя отменить. Убедитесь, что вы сохранили свой код, если он важен.</p>
      </div>
      <div class="modal-footer">
        <button id="author-solution-cancel-btn" class="modal-btn modal-btn-cancel">Отмена</button>
        <button id="author-solution-replace-btn" class="modal-btn modal-btn-confirm">Заменить код</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  modal.style.display = 'flex';

  const cancelBtn = document.getElementById('author-solution-cancel-btn');
  const replaceBtn = document.getElementById('author-solution-replace-btn');
  const modalOverlay = modal.querySelector('.modal-overlay');

  const closeModal = function() {
    modal.style.display = 'none';
    modal.remove();
    document.removeEventListener('keydown', handleEscapeKey);
  };

  const handleEscapeKey = function(e) {
    if (e.key === 'Escape') {
      closeModal();
    }
  };


  const handleReplace = function() {
    closeModal();
    replaceCodeWithAuthorSolution(solution);
  };

  cancelBtn.addEventListener('click', closeModal);
  replaceBtn.addEventListener('click', handleReplace);
  modalOverlay.addEventListener('click', closeModal);
  document.addEventListener('keydown', handleEscapeKey);
}


function replaceCodeWithAuthorSolution(solution) {
  if (!editor || !currentProblem) return;


  const processedSolution = processAuthorSolution(solution, currentProblem);


  editor.setValue(processedSolution);


  localStorage.setItem(`code_problem_${currentProblem.id}`, processedSolution);


  const model = editor.getModel();
  const lineCount = model.getLineCount();
  const lastLineLength = model.getLineContent(lineCount).length;
  editor.setPosition({ lineNumber: lineCount, column: lastLineLength + 1 });
  editor.focus();
}


function processAuthorSolution(solution, problem) {
  if (!problem || !problem.function) return solution;

  const lines = solution.split('\n');
  const funcName = problem.function;

  console.log('[AuthorSolution] Raw lines from file:');
  lines.forEach((line, i) => {
    console.log(`  Line ${i}: [${line}] (length: ${line.length}, first4: [${line.substring(0, 4)}])`);
  });


  const firstLine = lines[0] || '';
  const funcDefPattern = new RegExp(`^\\s*def\\s+${funcName}\\s*\\(`);

  if (funcDefPattern.test(firstLine)) {

    const bodyLines = lines.slice(1);


    const signature = generateFunctionSignature(problem);

    const result = signature + bodyLines.join('\n');
    console.log('[AuthorSolution] Result (case 1 - with def):', result);
    return result;
  }



  if (firstLine.startsWith('    ')) {

    const signature = generateFunctionSignature(problem);

    const result = signature + lines.join('\n');
    console.log('[AuthorSolution] Result (case 2 - indented body):', result);
    return result;
  }


  console.log('[AuthorSolution] Result (case 3 - plain):', solution);
  return solution;
}


function generateFunctionSignature(problem) {
  const funcName = problem.function || 'solution';
  const args = problem.arguments || [];
  const returnType = problem.return_type || 'Any';

  const argsStr = args.map(arg => `${arg.name}: ${arg.type}`).join(', ');


  return `def ${funcName}(${argsStr}) -> ${returnType}:\n`;
}


function showAuthorSolutionModal(solution) {

  const modal = document.createElement('div');
  modal.id = 'author-solution-modal';
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-overlay"></div>
    <div class="modal-content author-solution-modal-content">
      <div class="modal-header">
        <h3>Авторское решение</h3>
      </div>
      <div class="modal-body">
        <pre class="author-solution-code">${escapeHtml(solution)}</pre>
      </div>
      <div class="modal-footer">
        <button id="author-solution-close-btn" class="modal-btn modal-btn-confirm">Закрыть</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  modal.style.display = 'flex';

  const closeBtn = document.getElementById('author-solution-close-btn');
  const modalOverlay = modal.querySelector('.modal-overlay');

  const closeModal = function() {
    modal.style.display = 'none';
    modal.remove();
    document.removeEventListener('keydown', handleEscapeKey);
  };

  const handleEscapeKey = function(e) {
    if (e.key === 'Escape') {
      closeModal();
    }
  };

  closeBtn.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', closeModal);
  document.addEventListener('keydown', handleEscapeKey);
}


function formatArgs(args) {
  if (!Array.isArray(args)) {
    return `<code>${escapeHtml(JSON.stringify(args))}</code>`;
  }
  return args.map((arg, i) => {
    const argName = currentProblem?.arguments?.[i]?.name || `arg${i + 1}`;
    return `<span class="arg-name">${argName}</span>=<code>${escapeHtml(JSON.stringify(arg))}</code>`;
  }).join(', ');
}


function escapeHtml(str) {
  if (str === null || str === undefined) {
    return '';
  }
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}


backBtn.addEventListener('click', handleBackClick);
runBtn.addEventListener('click', runTests);


if (authorSolutionBtn) {
  authorSolutionBtn.addEventListener('click', function() {
    if (currentProblem && currentProblem.author_solution) {

      showAuthorSolutionConfirmation(currentProblem.author_solution);
    }
  });
}


if (resetStatsBtn) {
  resetStatsBtn.addEventListener('click', showResetStatisticsModal);
}


document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape' && workspaceView.style.display !== 'none') {

    const focusedElement = document.activeElement;
    const monacoWidget = focusedElement && (
      focusedElement.closest('.monaco-editor') &&
      (focusedElement.tagName === 'INPUT' || focusedElement.tagName === 'TEXTAREA')
    );


    if (monacoWidget) {
      return;
    }


    const modal = document.getElementById('confirm-modal');
    const modalIsOpen = modal && modal.classList.contains('show');

    if (modal && !modalIsOpen) {
      e.preventDefault();
      e.stopPropagation();
      showExitConfirmation();
    }
  }
});


function hasModifiedCode() {
  if (!currentProblem || !editor) {
    console.log('[AlgoTrainer] hasModifiedCode: no currentProblem or editor');
    return false;
  }
  const template = currentProblem.template || '';
  const currentCode = editor.getValue() || '';
  const modified = currentCode !== template && currentCode.trim() !== '';
  console.log('[AlgoTrainer] hasModifiedCode:', modified, '| template:', JSON.stringify(template), '| current:', JSON.stringify(currentCode));
  return modified;
}


function showExitConfirmation() {

  if (problemSolved || !hasModifiedCode()) {
    goBack();
    return;
  }


  const modal = document.getElementById('confirm-modal');
  if (!modal) {
    goBack();
    return;
  }
  const modalOverlay = modal.querySelector('.modal-overlay');
  const modalMessage = document.getElementById('modal-message');
  modalMessage.textContent = 'Do you really want to exit? Your code will be saved, but you will lose the current workspace view.';
  modal.classList.add('show');


  const cancelBtn = document.getElementById('modal-cancel-btn');
  const confirmBtn = document.getElementById('modal-confirm-btn');


  const newCancelBtn = cancelBtn.cloneNode(true);
  const newConfirmBtn = confirmBtn.cloneNode(true);
  cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
  confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

  newCancelBtn.addEventListener('click', function() {
    modal.classList.remove('show');
  });

  newConfirmBtn.addEventListener('click', function() {
    modal.classList.remove('show');
    goBack();
  });


  modalOverlay.addEventListener('click', function() {
    modal.classList.remove('show');
  });


  newCancelBtn.focus();


  const escapeHandler = function(e) {
    if (e.key === 'Escape') {
      modal.classList.remove('show');
      document.removeEventListener('keydown', escapeHandler);
    }
  };
  document.addEventListener('keydown', escapeHandler);
}


function handleBackClick() {
  showExitConfirmation();
}


function onPywebviewReady() {
  console.log('[AlgoTrainer] onPywebviewReady called');
  if (!pywebviewReady) {
    pywebviewReady = true;
    tryInit();
  }
}


function resetCodeToTemplate() {
  if (!currentProblem || !editor) return;

  const modal = document.getElementById('confirm-modal');
  const modalOverlay = modal.querySelector('.modal-overlay');
  const modalMessage = document.getElementById('modal-message');
  modalMessage.textContent = 'Reset code to initial template? This will clear your saved code for this problem.';
  modal.classList.add('show');


  const cancelBtn = document.getElementById('modal-cancel-btn');
  const confirmBtn = document.getElementById('modal-confirm-btn');


  const newCancelBtn = cancelBtn.cloneNode(true);
  const newConfirmBtn = confirmBtn.cloneNode(true);
  cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
  confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

  newCancelBtn.addEventListener('click', function() {
    modal.classList.remove('show');
  });

  newConfirmBtn.addEventListener('click', function() {
    modal.classList.remove('show');

    localStorage.removeItem(`code_problem_${currentProblem.id}`);


    const template = currentProblem.template || '';
    editor.setValue(template);


    const model = editor.getModel();
    const lineCount = model.getLineCount();

    let targetLine = lineCount;
    for (let i = lineCount; i >= 1; i--) {
      const content = model.getLineContent(i);
      if (content.trim() === '' && content.length > 0) {

        targetLine = i;
        break;
      }
    }

    const targetCol = model.getLineContent(targetLine).length + 1;
    editor.setPosition({ lineNumber: targetLine, column: targetCol });
    editor.focus();

    console.log('[AlgoTrainer] Code reset to template for problem', currentProblem.id);
  });


  modalOverlay.addEventListener('click', function() {
    modal.classList.remove('show');
  });


  newCancelBtn.focus();
}


window.addEventListener('pywebviewready', onPywebviewReady);

function clearProblemCache() {
  localStorage.removeItem('problem_summaries');
  localStorage.removeItem('problem_summaries_timestamp');
  console.log('[AlgoTrainer] Problem cache cleared. Reload to fetch fresh data.');
}


window.clearProblemCache = clearProblemCache;



if (typeof pywebview !== 'undefined' && pywebview.api) {
  console.log('[AlgoTrainer] pywebview already available at script load');
  onPywebviewReady();
} else {

  let pollCount = 0;
  const pollInterval = setInterval(function() {
    pollCount++;
    if (typeof pywebview !== 'undefined' && pywebview.api) {
      console.log('[AlgoTrainer] pywebview found via polling after ' + (pollCount * 100) + 'ms');
      clearInterval(pollInterval);
      onPywebviewReady();
    } else if (pollCount >= 100) {

      console.error('[AlgoTrainer] pywebview not found after 10 seconds');
      clearInterval(pollInterval);
      showError('Failed to connect to Python backend. Please restart the application.');
    }
  }, 100);
}
