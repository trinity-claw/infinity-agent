import React, { useEffect, useRef } from 'react';

const WebGLBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl');
    if (!gl) {
      console.warn("WebGL not supported");
      return;
    }

    // Vertex Shader
    const vsSource = `
      attribute vec4 aVertexPosition;
      void main() {
          gl_Position = aVertexPosition;
      }
    `;

    // Fragment Shader
    const fsSource = `
      precision mediump float;
      uniform vec2 u_resolution;
      uniform float u_time;
      
      void main() {
          vec2 st = gl_FragCoord.xy / u_resolution.xy;
          st.x *= u_resolution.x / u_resolution.y;
          
          vec3 color = vec3(0.0);
          
          // InfinitePay pure brand colors
          vec3 bg_color = vec3(0.098, 0.098, 0.098); // #191919
          
          // Primary: #00E676 (rgb: 0, 230, 118)
          vec3 primary_color = vec3(0.0, 0.902, 0.463);
          
          // Secondary: #00C853 (rgb: 0, 200, 83)
          vec3 secondary_color = vec3(0.0, 0.784, 0.325);
          
          vec2 pos = vec2(0.5 * u_resolution.x/u_resolution.y, 0.5);
          
          // Slow continuous pulsing
          float time_scale = u_time * 0.4;
          
          // Create overlapping soft rings
          float d1 = length(st - pos);
          float ring1 = sin(d1 * 10.0 - time_scale) * 0.5 + 0.5;
          float ring2 = sin(d1 * 15.0 - time_scale * 1.5) * 0.5 + 0.5;
          
          // Enhance the center glow
          float center_glow = 1.0 - smoothstep(0.0, 0.6, d1);
          
          // Mix colors with a subtle intensity
          vec3 wave_color = mix(primary_color, secondary_color, ring2);
          
          // Apply extreme attenuation to keep it strictly in the background
          float intensity = (ring1 * 0.03) + (ring2 * 0.02) + (center_glow * 0.05);
          
          color = mix(bg_color, wave_color, intensity);
          
          gl_FragColor = vec4(color, 1.0);
      }
    `;

    const compileShader = (gl, type, source) => {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader validation failed:', gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    };

    const vertexShader = compileShader(gl, gl.VERTEX_SHADER, vsSource);
    const fragmentShader = compileShader(gl, gl.FRAGMENT_SHADER, fsSource);

    const shaderProgram = gl.createProgram();
    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);

    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    const positions = [
      1.0,  1.0,
     -1.0,  1.0,
      1.0, -1.0,
     -1.0, -1.0,
    ];
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);

    const positionAttributeLocation = gl.getAttribLocation(shaderProgram, "aVertexPosition");
    const resolutionUniformLocation = gl.getUniformLocation(shaderProgram, "u_resolution");
    const timeUniformLocation = gl.getUniformLocation(shaderProgram, "u_time");

    let animationFrameId;

    const render = (time) => {
      // Resize canvas to match display size
      const displayWidth  = canvas.clientWidth;
      const displayHeight = canvas.clientHeight;
      if (canvas.width  !== displayWidth || canvas.height !== displayHeight) {
        canvas.width  = displayWidth;
        canvas.height = displayHeight;
        gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
      }

      gl.useProgram(shaderProgram);
      gl.enableVertexAttribArray(positionAttributeLocation);
      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
      gl.vertexAttribPointer(positionAttributeLocation, 2, gl.FLOAT, false, 0, 0);

      gl.uniform2f(resolutionUniformLocation, gl.canvas.width, gl.canvas.height);
      gl.uniform1f(timeUniformLocation, time * 0.001);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} id="webgl-canvas"></canvas>;
};

export default WebGLBackground;
