/* TRUSTX — Plexus Network Animation */
(function () {
    const canvas = document.getElementById('trustix-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const CFG = {
        count:       90,
        speed:       0.35,
        dotR:        2.2,
        linkDist:    160,
        dotColor:    'rgba(255,255,255,',
        lineColor:   'rgba(63,185,80,',
    };

    let W, H, dots;

    function resize() {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }

    function mkDot() {
        const a = Math.random() * Math.PI * 2;
        const s = CFG.speed * (0.4 + Math.random() * 0.6);
        return {
            x: Math.random() * W,
            y: Math.random() * H,
            vx: Math.cos(a) * s,
            vy: Math.sin(a) * s,
            r: CFG.dotR * (0.6 + Math.random() * 0.8),
        };
    }

    function init() {
        resize();
        dots = Array.from({ length: CFG.count }, mkDot);
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);

        // move
        dots.forEach(d => {
            d.x += d.vx; d.y += d.vy;
            if (d.x < 0) d.x = W; if (d.x > W) d.x = 0;
            if (d.y < 0) d.y = H; if (d.y > H) d.y = 0;
        });

        // lines
        for (let i = 0; i < dots.length; i++) {
            for (let j = i + 1; j < dots.length; j++) {
                const dx = dots[i].x - dots[j].x;
                const dy = dots[i].y - dots[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < CFG.linkDist) {
                    const alpha = (1 - dist / CFG.linkDist) * 0.45;
                    ctx.beginPath();
                    ctx.moveTo(dots[i].x, dots[i].y);
                    ctx.lineTo(dots[j].x, dots[j].y);
                    ctx.strokeStyle = CFG.lineColor + alpha + ')';
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }
        }

        // dots
        dots.forEach(d => {
            ctx.beginPath();
            ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
            ctx.fillStyle = CFG.dotColor + '0.75)';
            ctx.fill();
        });

        requestAnimationFrame(draw);
    }

    window.addEventListener('resize', () => { resize(); });
    init();
    draw();
})();
