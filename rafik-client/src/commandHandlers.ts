import * as vscode from 'vscode';

// Define the shape of a handler function
type HandlerFunction = (editor: vscode.TextEditor, params: any[]) => void;

// --- THE WORKERS ---

const handleMoveCursor: HandlerFunction = (editor, params) => {
    const unit = params[0];      // "line", "char"
    const qty = parseInt(params[1]);
    const direction = params[2]; // "up", "down", "left", "right"

    const currentPos = editor.selection.active;
    let newPos = currentPos;

    if (unit === 'line') {
        if (direction === 'down') newPos = currentPos.translate(qty, 0);
        if (direction === 'up') newPos = currentPos.translate(-qty, 0);
    } else if (unit === 'char') {
        if (direction === 'right') newPos = currentPos.translate(0, qty);
        if (direction === 'left') newPos = currentPos.translate(0, -qty);
    }

    editor.selection = new vscode.Selection(newPos, newPos);
    editor.revealRange(new vscode.Range(newPos, newPos));
};

const handleJumpToLine: HandlerFunction = (editor, params) => {
    const lineNum = parseInt(params[0]) - 1; // VS Code is 0-indexed
    const newPos = new vscode.Position(lineNum, 0);
    editor.selection = new vscode.Selection(newPos, newPos);
    editor.revealRange(new vscode.Range(newPos, newPos), vscode.TextEditorRevealType.InCenter);
};

const handleScroll: HandlerFunction = (editor, params) => {
    const direction = params[0] === "down" ? 'down' : 'up';
    vscode.commands.executeCommand('editorScroll', { to: direction, by: 'line', value: 5 });
};

// --- NEW FEATURES GO HERE ---
// Example:
// const handleInsertFunction: HandlerFunction = (editor, params) => { ... }


// --- THE REGISTRY (Export this!) ---
export const CommandRegistry: { [key: string]: HandlerFunction } = {
    "MOVE_CURSOR": handleMoveCursor,
    "JUMP_TO_LINE": handleJumpToLine,
    "SCROLL": handleScroll,
    // Add new commands here:
    // "INSERT_FUNCTION": handleInsertFunction
};