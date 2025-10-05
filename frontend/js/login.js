<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta http-equiv="Content-Style-Type" content="text/css">
  <title></title>
  <meta name="Generator" content="Cocoa HTML Writer">
  <meta name="CocoaVersion" content="2685.1">
  <style type="text/css">
    p.p1 {margin: 0.0px 0.0px 0.0px 0.0px; font: 12.0px Helvetica; -webkit-text-stroke: #000000}
    p.p2 {margin: 0.0px 0.0px 0.0px 0.0px; font: 12.0px Helvetica; -webkit-text-stroke: #000000; min-height: 14.0px}
    span.s1 {font-kerning: none}
    span.s2 {font: 12.0px 'Apple Color Emoji'; font-kerning: none}
  </style>
</head>
<body>
<p class="p1"><span class="s1">const serverStatus = document.getElementById("serverStatus");</span></p>
<p class="p1"><span class="s1">const loginForm = document.getElementById("loginForm");</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1">// </span><span class="s2">✅</span><span class="s1"> Check server connection</span></p>
<p class="p1"><span class="s1">async function checkServerStatus() {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>try {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>const res = await fetch("http://127.0.0.1:8000/ping");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>if (res.ok) {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>serverStatus.classList.remove("alert-danger");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>serverStatus.classList.add("alert-success");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>serverStatus.textContent = "</span><span class="s2">✅</span><span class="s1"> Server Connected";</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>} else {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>throw new Error();</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>}</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>} catch {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>serverStatus.classList.remove("alert-success");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>serverStatus.classList.add("alert-danger");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>serverStatus.textContent = "</span><span class="s2">❌</span><span class="s1"> Server Offline";</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>}</span></p>
<p class="p1"><span class="s1">}</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1">// Run connection check every 5 seconds</span></p>
<p class="p1"><span class="s1">checkServerStatus();</span></p>
<p class="p1"><span class="s1">setInterval(checkServerStatus, 5000);</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1">// </span><span class="s2">🧩</span><span class="s1"> Handle login form submission</span></p>
<p class="p1"><span class="s1">loginForm.addEventListener("submit", async (e) =&gt; {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>e.preventDefault();</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>const email = document.getElementById("email").value.trim();</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>const password = document.getElementById("password").value.trim();</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>const formData = new FormData();</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>formData.append("email", email);</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>formData.append("password", password);</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>try {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>const res = await fetch("http://127.0.0.1:8000/login", {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>method: "POST",</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>body: formData,</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>});</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>if (!res.ok) {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>const error = await res.json();</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>alert("Login failed: " + error.detail);</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>return;</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>}</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>const data = await res.json();</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>console.log("Login response:", data);</span></p>
<p class="p2"><span class="s1"></span><br></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>// Redirect based on user role</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>switch (data.role) {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>case "coach":</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>window.location.href = `coach_dashboard.html?coach_id=${data.id}`;</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>break;</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>case "admin":</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>alert("Admin dashboard coming soon!");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>break;</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>case "coach_org":</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>alert("Coach organization dashboard coming soon!");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>break;</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>case "coachee_org":</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>alert("Coachee organization dashboard coming soon!");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>break;</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>case "coachee":</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>alert("Coachee dashboard coming soon!");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>break;</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">      </span>default:</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">        </span>alert("Unknown user type.");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>}</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>} catch (error) {</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">    </span>alert("Error connecting to server. Check if backend is running.");</span></p>
<p class="p1"><span class="s1"><span class="Apple-converted-space">  </span>}</span></p>
<p class="p1"><span class="s1">});</span></p>
</body>
</html>
