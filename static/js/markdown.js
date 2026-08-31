/**
 * Safe XSS-proof Markdown formatter.
 * Escapes raw HTML before applying structural markdown elements.
 */

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

export function renderMarkdown(markdownText) {
    if (!markdownText) return '';

    // Step 1: Escape HTML entities first for safety
    let safeText = escapeHtml(markdownText);

    // Step 2: Bold text (**text**)
    safeText = safeText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Step 3: Inline code (`code`)
    safeText = safeText.replace(/`(.*?)`/g, '<code>$1</code>');

    // Step 4: Headings (### Heading)
    safeText = safeText.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    safeText = safeText.replace(/^## (.*$)/gim, '<h3>$1</h3>');

    // Step 5: Unordered lists (* item or - item)
    const lines = safeText.split('\n');
    let inList = false;
    let resultLines = [];

    for (let line of lines) {
        const listMatch = line.match(/^[\*\-]\s+(.*)/);
        if (listMatch) {
            if (!inList) {
                resultLines.push('<ul>');
                inList = true;
            }
            resultLines.push(`<li>${listMatch[1]}</li>`);
        } else {
            if (inList) {
                resultLines.push('</ul>');
                inList = false;
            }
            resultLines.push(line);
        }
    }
    if (inList) {
        resultLines.push('</ul>');
    }

    safeText = resultLines.join('\n');

    // Step 6: Paragraphs (split by double newlines)
    const paragraphs = safeText.split(/\n\s*\n/);
    const htmlOutput = paragraphs
        .map(p => {
            const trimmed = p.trim();
            if (!trimmed) return '';
            if (trimmed.startsWith('<h3>') || trimmed.startsWith('<ul>')) {
                return trimmed;
            }
            return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
        })
        .filter(Boolean)
        .join('');

    return htmlOutput;
}
