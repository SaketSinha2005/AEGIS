import os
import ast
from typing import TypedDict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="HaltState AI Generation Engine")

class GraphState(TypedDict):
    problem_statement: str
    generated_code: Optional[str]
    error_message: Optional[str]
    iterations: int

class ProblemRequest(BaseModel):
    problem: str

class GenerationResponse(BaseModel):
    code: str
    iterations: int
    status: str

llm = ChatOpenAI(model="gpt-4o", temperature=0.1)


def generate_code_node(state: GraphState) -> GraphState:
    """Node that uses LangChain to generate Python code based on the problem or error."""
    iterations = state.get("iterations", 0) + 1
    
    if state.get("error_message"):
        system_msg = (
            "You are an expert Python programmer. The previous code you generated had a syntax error. "
            "Fix the code and return ONLY the executable Python code inside standard python markdown blocks. "
            "Do not include any explanations, introductory text, or closing text."
        )
        user_msg = f"Problem:\n{state['problem_statement']}\n\nFailed Code:\n{state['generated_code']}\n\nSyntax Error:\n{state['error_message']}"
    else:
        system_msg = (
            "You are an expert Python programmer. Generate standard executable Python code that solves the user's problem statement. "
            "Your output must contain ONLY the valid Python code inside standard code blocks. "
            "Do not include any explanations, markdown text outside the code block, or introductory text."
        )
        user_msg = f"Problem Statement:\n{state['problem_statement']}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", user_msg)
    ])
    
    chain = prompt | llm
    response = chain.invoke({})
    
    raw_content = response.content.strip()
    clean_code = raw_content
    if "```python" in raw_content:
        clean_code = raw_content.split("```python")[1].split("```")[0].strip()
    elif "```" in raw_content:
        clean_code = raw_content.split("```")[1].split("```")[0].strip()

    return {
        **state,
        "generated_code": clean_code,
        "iterations": iterations,
        "error_message": None  
    }

def validate_syntax_node(state: GraphState) -> GraphState:
    """Node that validates if the generated code is syntactically correct Python code."""
    code = state["generated_code"]
    try:
        ast.parse(code)
        return {**state, "error_message": None}
    except SyntaxError as e:
        return {**state, "error_message": f"SyntaxError: {e.msg} on line {e.lineno}"}


def decide_next_step(state: GraphState) -> str:
    """Determines whether to loop back for correction or finish."""
    if state["error_message"] and state["iterations"] < 3:
        return "generate"
    return END

workflow = StateGraph(GraphState)

workflow.add_node("generate", generate_code_node)
workflow.add_node("validate", validate_syntax_node)

workflow.set_entry_point("generate")

workflow.add_edge("generate", "validate")
workflow.add_conditional_edges(
    "validate",
    decide_next_step,
    {
        "generate": "generate",
        END: END
    }
)

graph = workflow.compile()

@app.post("/api/v1/generate", response_model=GenerationResponse)
async def generate_problem_solution(request: ProblemRequest):
    initial_state: GraphState = {
        "problem_statement": request.problem,
        "generated_code": None,
        "error_message": None,
        "iterations": 0
    }
    
    try:
        final_state = graph.invoke(initial_state)
        
        if final_state.get("error_message"):
            raise HTTPException(
                status_code=422, 
                detail=f"AI failed to generate syntactically valid code: {final_state['error_message']}"
            )
            
        return GenerationResponse(
            code=final_state["generated_code"],
            iterations=final_state["iterations"],
            status="success"
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)