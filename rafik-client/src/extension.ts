import * as vscode from 'vscode';
import * as http from 'http';
import { CommandRegistry } from './commandHandlers'; // Import the registry

let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {
    outputChannel = vscode.window.createOutputChannel("Rafik Monitor");
    outputChannel.show(true);
    outputChannel.appendLine("✅ Rafik Modular Client ACTIVATED");

    // Poll every 500ms
    const interval = setInterval(pollServer, 500);
    context.subscriptions.push({ dispose: () => clearInterval(interval) });
}

function pollServer() {
    http.get('http://127.0.0.1:8000/fetch_command', (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
            try {
                const json = JSON.parse(data);
                if (json.type !== "EMPTY") {
                    outputChannel.appendLine(`🚀 RECEIVED: ${json.type}`);
                    dispatchCommand(json);
                }
            } catch (e) {
                outputChannel.appendLine(`❌ Parse Error: ${e}`);
            }
        });
    }).on("error", err => outputChannel.appendLine(`❌ Connection Error: ${err.message}`));
}

function dispatchCommand(cmd: any) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        outputChannel.appendLine("⚠️ No active editor!");
        return;
    }

    // --- THE MAGIC: DYNAMIC DISPATCH ---
    // Look up the function in the registry using the string "MOVE_CURSOR"
    const handler = CommandRegistry[cmd.type];

    if (handler) {
        try {
            // Run the worker function
            handler(editor, cmd.params);
            outputChannel.appendLine(`✅ Executed ${cmd.type}`);
        } catch (error) {
            outputChannel.appendLine(`❌ Error in handler for ${cmd.type}: ${error}`);
        }
    } else {
        outputChannel.appendLine(`⚠️ Unknown Command: ${cmd.type}. Did you register it in commandHandlers.ts?`);
    }
}

export function deactivate() {}