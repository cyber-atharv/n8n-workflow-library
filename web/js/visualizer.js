/**
 * web/js/visualizer.js
 * Interactive SVG Node Graph Visualizer for n8n workflows.
 * Renders nodes, wires, triggers, and ports with pan and zoom.
 */

class WorkflowVisualizer {
  constructor(svgElementId) {
    this.svg = document.getElementById(svgElementId);
    this.scale = 1;
    this.panX = 40;
    this.panY = 40;
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;

    this.initEvents();
  }

  initEvents() {
    if (!this.svg) return;

    this.svg.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.startX = e.clientX - this.panX;
      this.startY = e.clientY - this.panY;
    });

    window.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      this.panX = e.clientX - this.startX;
      this.panY = e.clientY - this.startY;
      this.updateTransform();
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    this.svg.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      this.zoom(zoomFactor, e.clientX, e.clientY);
    });
  }

  zoom(factor) {
    this.scale = Math.min(Math.max(0.3, this.scale * factor), 2.5);
    this.updateTransform();
  }

  reset(minX = 0, minY = 0) {
    this.scale = 0.85;
    this.panX = 60 - minX * this.scale;
    this.panY = 60 - minY * this.scale;
    this.updateTransform();
  }

  updateTransform() {
    const rootG = this.svg.querySelector('g.graph-root');
    if (rootG) {
      rootG.setAttribute('transform', `translate(${this.panX}, ${this.panY}) scale(${this.scale})`);
    }
  }

  render(workflowData) {
    if (!this.svg) return;
    this.svg.innerHTML = '';

    const wfObj = (workflowData.workflow && workflowData.workflow.nodes) ? workflowData.workflow : workflowData;
    const nodes = wfObj.nodes || [];
    const connections = wfObj.connections || {};

    if (nodes.length === 0) {
      this.svg.innerHTML = `<text x="50%" y="50%" fill="#94a3b8" text-anchor="middle" font-family="sans-serif">No node layout data available.</text>`;
      return;
    }

    const nodeWidth = 200;
    const nodeHeight = 64;

    // Check positions and compute layout bounds
    let hasPositions = nodes.some(n => Array.isArray(n.position) && n.position.length >= 2);
    let nodeMap = {};
    let minX = Infinity, minY = Infinity;

    nodes.forEach((node, idx) => {
      let x = idx * 240 + 50;
      let y = 150;
      if (hasPositions && Array.isArray(node.position) && node.position.length >= 2) {
        x = node.position[0];
        y = node.position[1];
      }
      nodeMap[node.name] = {
        node,
        x,
        y,
        width: nodeWidth,
        height: nodeHeight
      };
      if (x < minX) minX = x;
      if (y < minY) minY = y;
    });

    const rootG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    rootG.setAttribute('class', 'graph-root');

    // Draw connection lines (curved bezier paths)
    const connG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    connG.setAttribute('class', 'connections-layer');

    Object.keys(connections).forEach(sourceName => {
      const sourceObj = nodeMap[sourceName];
      if (!sourceObj) return;

      const connGroup = connections[sourceName];
      // iterate outputs (main, ai_languageModel, etc.)
      Object.keys(connGroup).forEach(outType => {
        const routes = connGroup[outType];
        if (Array.isArray(routes)) {
          routes.forEach(destArr => {
            if (Array.isArray(destArr)) {
              destArr.forEach(target => {
                const targetObj = nodeMap[target.node];
                if (!targetObj) return;

                const startX = sourceObj.x + sourceObj.width;
                const startY = sourceObj.y + sourceObj.height / 2;
                const endX = targetObj.x;
                const endY = targetObj.y + targetObj.height / 2;

                const dx = Math.abs(endX - startX) * 0.5;
                const d = `M ${startX} ${startY} C ${startX + dx} ${startY}, ${endX - dx} ${endY}, ${endX} ${endY}`;

                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', d);
                path.setAttribute('fill', 'none');
                path.setAttribute('stroke', outType.includes('ai') ? '#a78bfa' : '#ff6d5a');
                path.setAttribute('stroke-width', '2.5');
                path.setAttribute('stroke-opacity', '0.75');
                path.setAttribute('stroke-dasharray', outType.includes('ai') ? '4 2' : 'none');
                connG.appendChild(path);
              });
            }
          });
        }
      });
    });

    rootG.appendChild(connG);

    // Draw Nodes
    const nodesG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    nodesG.setAttribute('class', 'nodes-layer');

    Object.values(nodeMap).forEach(item => {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('transform', `translate(${item.x}, ${item.y})`);
      g.style.cursor = 'pointer';

      // Card Background
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('width', item.width);
      rect.setAttribute('height', item.height);
      rect.setAttribute('rx', '8');
      rect.setAttribute('fill', '#161f30');
      rect.setAttribute('stroke', item.node.type.includes('trigger') ? '#ff6d5a' : '#2d3b55');
      rect.setAttribute('stroke-width', '1.5');
      g.appendChild(rect);

      // Node Type Icon Indicator
      const iconRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      iconRect.setAttribute('x', '10');
      iconRect.setAttribute('y', '14');
      iconRect.setAttribute('width', '36');
      iconRect.setAttribute('height', '36');
      iconRect.setAttribute('rx', '6');
      iconRect.setAttribute('fill', item.node.type.includes('trigger') ? 'rgba(255, 109, 90, 0.2)' : 'rgba(59, 130, 246, 0.15)');
      g.appendChild(iconRect);

      // Node Name Label
      const titleText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      titleText.setAttribute('x', '54');
      titleText.setAttribute('y', '28');
      titleText.setAttribute('fill', '#ffffff');
      titleText.setAttribute('font-size', '12');
      titleText.setAttribute('font-weight', '600');
      titleText.setAttribute('font-family', 'sans-serif');
      titleText.textContent = item.node.name.length > 18 ? item.node.name.substring(0, 16) + '...' : item.node.name;
      g.appendChild(titleText);

      // Sub-label (Node Type)
      const typeParts = item.node.type.split('.');
      const cleanType = typeParts[typeParts.length - 1];
      const subText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      subText.setAttribute('x', '54');
      subText.setAttribute('y', '44');
      subText.setAttribute('fill', '#94a3b8');
      subText.setAttribute('font-size', '10');
      subText.setAttribute('font-family', 'monospace');
      subText.textContent = cleanType.length > 20 ? cleanType.substring(0, 18) + '...' : cleanType;
      g.appendChild(subText);

      // Port circles
      const inPort = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      inPort.setAttribute('cx', '0');
      inPort.setAttribute('cy', item.height / 2);
      inPort.setAttribute('r', '4');
      inPort.setAttribute('fill', '#64748b');
      g.appendChild(inPort);

      const outPort = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      outPort.setAttribute('cx', item.width);
      outPort.setAttribute('cy', item.height / 2);
      outPort.setAttribute('r', '4');
      outPort.setAttribute('fill', '#ff6d5a');
      g.appendChild(outPort);

      nodesG.appendChild(g);
    });

    rootG.appendChild(nodesG);
    this.svg.appendChild(rootG);

    this.reset(minX === Infinity ? 0 : minX, minY === Infinity ? 0 : minY);
  }
}
