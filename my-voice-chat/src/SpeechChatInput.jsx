import React, { useRef, useState } from "react";

const SpeechChatInput = ({ onSend }) => {
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  const getRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("이 브라우저는 음성 인식을 지원하지 않습니다. 크롬/엣지/사파리에서 사용하세요.");
      return null;
    }
    if (!recognitionRef.current) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.lang = "ko-KR";
      recognitionRef.current.interimResults = false;
      recognitionRef.current.onresult = (event) => {
        const text = event.results[0][0].transcript;
        setInput((prev) => prev + text);
      };
      recognitionRef.current.onend = () => setListening(false);
      recognitionRef.current.onerror = () => setListening(false);
    }
    return recognitionRef.current;
  };

  const handleMicClick = () => {
    const recognition = getRecognition();
    if (!recognition) return;
    if (!listening) {
      recognition.start();
      setListening(true);
    } else {
      recognition.stop();
      setListening(false);
    }
  };

  const handleSend = () => {
    if (input.trim()) {
      onSend(input.trim());
      setInput("");
    }
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        style={{ flex: 1, fontSize: 18, padding: 8 }}
        placeholder="메시지를 입력하거나 마이크를 눌러보세요"
      />
      <button onClick={handleMicClick} style={{ fontSize: 22 }}>
        {listening ? "🎤(녹음중)" : "🎤"}
      </button>
      <button onClick={handleSend} style={{ fontSize: 18 }}>
        전송
      </button>
    </div>
  );
};

export default SpeechChatInput;
