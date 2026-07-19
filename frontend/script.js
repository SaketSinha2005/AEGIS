console.log("Hello");

const backendURL = "http://127.0.0.1:8000/execute";

const runButton = document.getElementById("run-btn");
const problemInput = document.getElementById("problem");
const generatedCode = document.getElementById("generated-code");
const terminalOutput = document.getElementById("terminal-output");
const clearButton = document.getElementById("clear-btn");
const copyButton = document.getElementById("copy-btn");
const downloadButton = document.getElementById("download-btn");

runButton.addEventListener("click", executeProblem);
problemInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault(); 
        executeProblem();       
    }
});

async function executeProblem() {
    const problem = problemInput.value.trim();

    if (problem === "") {
        alert("Please enter a problem statement.");
        return;
    }

    // 1. Grab the progress indicator from the DOM
    const progressIndicator = document.getElementById("progress-indicator");

    runButton.disabled = true;
    runButton.innerHTML = `<span class="material-symbols-outlined text-[20px] animate-spin">sync</span> Running...`;

    generatedCode.textContent = "";
    
    // 2. Show the loading bar and clear the terminal text
    progressIndicator.classList.remove("hidden");
    terminalOutput.innerHTML = "Generating code...\n";

    try {
        const response = await fetch(backendURL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                problem: problem
            })
        });

        const result = await response.json();

        if (!response.ok) {
            // This grabs the "Execution timed out." detail from your FastAPI backend
            throw new Error(result.detail || "Execution failed."); 
        }

        generatedCode.textContent = result.generated_code;

        // Render Success or Docker Error
        if (result.exit_code === 0) {
            terminalOutput.innerHTML = `
                <span class="text-green-400 mr-2">[SUCCESS]</span> Execution completed successfully.<br/>
                <div class="mt-2 pl-2 border-l-2 border-zinc-700 text-on-surface">
                    ${result.stdout.replace(/\n/g, '<br/>') || 'No output generated.'}
                </div>
            `;
        } else {
            terminalOutput.innerHTML = `
                <span class="text-error mr-2">[ERROR]</span> Process failed with code ${result.exit_code}.<br/>
                <div class="mt-2 pl-2 border-l-2 border-error/50 text-error/90">
                    ${result.stderr.replace(/\n/g, '<br/>') || result.stdout.replace(/\n/g, '<br/>')}
                </div>
            `;
        }

    } catch (error) {
        // Catch the timeout or network errors
        if (error.message.toLowerCase().includes("timed out") || error.message.toLowerCase().includes("timeout")) {
            terminalOutput.innerHTML = `
                <span class="text-yellow-500 mr-2">[TIMEOUT]</span>
                <br/>
                Execution exceeded maximum time limit (15s). Process terminated.
            `;
        } else {
            // If you see "Failed to fetch" here, it means CORS isn't configured right in main.py
            terminalOutput.innerHTML = `
                <span class="text-error mr-2">[ERROR]</span>
                <br/>
                ${error.message}
            `;
        }
    } finally {
        // 3. Hide the loading bar and restore the original button HTML
        progressIndicator.classList.add("hidden");
        runButton.disabled = false;
        runButton.innerHTML = `<span class="material-symbols-outlined text-[20px]">bolt</span> Generate & Execute`;
    }
}

clearButton.addEventListener("click", () => {
    problemInput.value = "";
});

copyButton.addEventListener("click", async () => {
    const codeToCopy = generatedCode.textContent;
    
    if (!codeToCopy) return; 

    try {
        await navigator.clipboard.writeText(codeToCopy);
        
        const tooltip = copyButton.querySelector("div");
        const originalText = tooltip.textContent;
        tooltip.textContent = "Copied!";
        setTimeout(() => tooltip.textContent = originalText, 2000);
    } catch (err) {
        console.error("Failed to copy text: ", err);
    }
});

downloadButton.addEventListener("click", () => {
    const codeToDownload = generatedCode.textContent;
    
    if (!codeToDownload) return;

    const blob = new Blob([codeToDownload], { type: "text/x-python" });
    
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "solution.py"; 
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
});

