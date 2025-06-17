document.addEventListener("DOMContentLoaded", () => {

    // 채팅 메시지 전송
    const sendBtn = document.getElementById("sendBtn"); // 보내기 버튼
    const userInput = document.getElementById("userInput"); // 유저 입력값
    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            sendMessage().catch(err => console.error(err));
        }
    });

    // =========[전역 변수]===========
    // 주요 DOM 요소들을 변수에 저장
    const chatList = document.getElementById("chatList"); // 채팅목록 리스트
    const chatHeader = document.getElementById("chatHeader"); // chat-area 새 채팅 버튼
    const newChatBtn = document.getElementById("newChatBtn"); // side-bar 새 채팅 버튼
    const messages = document.getElementById("messages"); // message가 입력되는 공간
    // 모달 관련 요소들
    const modalOverlay = document.getElementById("modalOverlay");
    const modalInput = document.getElementById("modalInput"); // 채팅방 제목 입력값
    const modalCancel = document.getElementById("modalCancel");
    const modalOk = document.getElementById("modalOk");

    let currentChatRoomIdx = null;
    let currentUserName = null;
    let currentUserIdx = null;
    let editingChatItem = null; // 편집중인 아이템 저장용

    // [1] 초기화 함수
    function init() {
        currentUserName = sessionStorage.getItem("userName");
        currentUserIdx = sessionStorage.getItem("userIdx");
        loadChatRooms();
    }

    init();


    // [2] 채팅방 목록 불러오기 함수
    async function loadChatRooms() {

        const userIdx = sessionStorage.getItem("userIdx");
        if (!userIdx) {
            return;
        }

        try {
            const response = await fetch(`/chat/${userIdx}`);
            if (!response.ok) throw new Error("응답 실패");

            const chatRooms = await response.json(); // ✅ 한 번만 호출
            if (chatRooms.length === 0) {
                chatList.innerHTML = "<p>채팅방이 없습니다. <br>새 채팅방을 만들어주세요!</p>";
            } else {
                renderChatRooms(chatRooms);
            }
        } catch (error) {
            console.error("채팅방 목록 불러오기 실패", error);
        }

    }

    // [3] 채팅방 목록 랜더링 함수
    function renderChatRooms(chatRooms) {

        console.log("렌더링할 채팅방 목록:", chatRooms);

        if (!Array.isArray(chatRooms)) {
            console.warn("chatRooms is not an array", chatRooms);
            return;
        }

        chatList.innerHTML = ""; // 기존 목록 초기화

        // 최신 순으로 정렬
        // sort((a, b) => b - a)는 내림차순 -> 자바스크립트에서 Date 객체를 빼면 밀리초 차이 (숫자)로 나옴
        // ---> b - a > 0이면 → b가 더 최신 b 가 앞으로 옴
        // sort((a, b) => a - b)는 오름차순
        chatRooms.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

        chatRooms.forEach((room) => {
            const item = createChatItem(room.croomTitle, room.croomIdx); // 제목과 ID 전달
            chatList.appendChild(item);
        });
    }

    // [3] 채팅 아이템 생성 및 이벤트 바인딩
    function createChatItem(croomTitle, croomIdx) {

        let title = croomTitle; // 제목

        // 요소 생성
        const item = document.createElement("div");
        item.className = "chat-item";
        item.dataset.croomIdx = croomIdx; // 고유 ID 저장

        // 📁 아이콘 이미지
        const icon = document.createElement("img");
        icon.className = "chat-icon";
        icon.src = "assets/img/directory.png"; // 아이콘 경로 변경 가능
        icon.alt = "폴더";

        // 제목 span
        const nameSpan = document.createElement("span");
        nameSpan.className = "chat-name";
        nameSpan.textContent = title;

        // 삭제 버튼
        const delBtn = document.createElement("span");
        delBtn.className = "delete-btn";
        delBtn.textContent = "X";

        item.append(icon, nameSpan, delBtn);

        // 클릭 -> 해당 채팅방 선택
        item.addEventListener("click", () => selectChat(title, croomIdx));

        // 더블클릭 ->  모달로 제목 수정
        item.addEventListener("dblclick", (e) => {
            e.stopPropagation();
            editingChatItem = item;   // 수정 중인 아이템 저장
            modalInput.value = title; // 기존 제목을 input에 넣기
            openModal();
        });

        // 클릭 -> 삭제버튼
        delBtn.addEventListener("click", (e) => {
            e.stopPropagation();

            if (chatHeader.textContent === title) {
                selectChat("새 채팅", null); // 채팅창 초기화
            }

            fetch(`/chat/delete/${croomIdx}`)
                .then(response => {
                    if (response.ok) {
                        item.remove(); // ✅ 정상 삭제
                        loadChatRooms(); // ✅ 삭제 후 목록 새로고침
                    } else {
                        console.error("삭제 실패:", response.statusText);
                    }
                })
                .catch(error => {
                    console.error("삭제 요청 중 오류 발생:", error);
                });
        });

        return item;
    }

    // [4] 채팅 선택 시 초기화 및 메시지 랜더링
    async function selectChat(title, croomIdx) {
        const chatTitle = document.getElementById("chatTitle");

        chatTitle.textContent = title; // 헤더에 채팅 제목 설정
        chatTitle.dataset.croomIdx = croomIdx; // ✅ 현재 채팅방 ID를 dataset으로 저장
        messages.innerHTML = "";  // 채팅방 비우기


        currentChatRoomIdx = croomIdx;

        // 채팅 내용이 없을 때 (새 채팅방)
        if (!croomIdx) {
            const botMsg = document.createElement("div"); // 빈 <div></div> 요소를 만들고
            botMsg.className = "ChatBot";
            botMsg.textContent = "안녕하세요! 무엇을 도와드릴까요?";
            messages.appendChild(botMsg);
        } else {
            // 서버에서 해당 채팅방 메시지 불러오기 로직
            try {
                const response = await fetch(`/chat/messages/${croomIdx}`)
                const chatMessages = await response.json();


                chatMessages.forEach(msg => {
                    const msgDiv = document.createElement("div");
                    msgDiv.classList.add("message");

                    if (msg.chatter === "ChatBot") {

                        // 봇 메시지는 <br><br> 기준으로 문단 분리
                        const paragraphs = msg.chat.split(/<br\s*\/?>\s*<br\s*\/?>/i);

                        const botMsgContainer = document.createElement("div");
                        botMsgContainer.classList.add("message", "bot");

                        paragraphs.forEach(p => {
                            const para = document.createElement("p");
                            para.style.margin = "12px 0";
                            para.innerHTML = p.trim().replace(/ /g, "&nbsp;");
                            botMsgContainer.appendChild(para);
                        });

                        messages.appendChild(botMsgContainer);

                    } else {
                        // 유저 메시지는 그대로 출력
                        const msgDiv = document.createElement("div");
                        msgDiv.classList.add("message", "user");
                        msgDiv.textContent = msg.chat;
                        messages.appendChild(msgDiv);
                    }
                })
            } catch (err) {
                console.log("채팅 메시지 로드 오류:", err);
            }


        }

    }

    // [5] 메시지 전송 핸들러
    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // 1. 사용자 메시지 append
        const userMessage = document.createElement("div");
        userMessage.className = "message user";
        userMessage.textContent = text;
        messages.appendChild(userMessage);

        userInput.value = "";
        messages.scrollTop = messages.scrollHeight;

        try {
            // 채팅방이 없으면 새 채팅방으로 생성
            if (!currentChatRoomIdx) {
                const createRoomRes = await fetch('/chat/create', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({title: "새 채팅방"})
                });

                if (!createRoomRes.ok) throw new Error("채팅방 생성 실패");

                const roomData = await createRoomRes.json();
                currentChatRoomIdx = roomData.croomIdx;

                // ✅ 전체 채팅방 목록을 새로 불러와 다시 렌더링
                await loadChatRooms();

            }

            // ... 응답 대기중 출력
            const loadingMessage = document.createElement("div");
            loadingMessage.className = "message bot";
            loadingMessage.textContent = "답변 생성중 입니다.";
            messages.appendChild(loadingMessage);
            messages.scrollTop = messages.scrollHeight;

            // 2. 메시지 전송 및 저장
            const sendMsgRes = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    croomIdx: currentChatRoomIdx,
                    chatter: currentUserIdx,
                    chat: text
                })
            });

            // 3. 챗봇 응답 메시지 append
            if (!sendMsgRes.ok) throw new Error("메시지 전송 실패");

            // chatBot 응답 데이터
            const resData = await sendMsgRes.json();

            // --- '답변 생성중 입니다' 제거 후 타이핑 출력 ---
            loadingMessage.textContent = "";

            const rawReply = resData.chat;

            // 1. <br><br>을 기준으로 문단 나눔
            const paragraphs = rawReply.split(/<br\s*\/?>\s*<br\s*\/?>/i);

            let paraIndex = 0;
            let charIndex = 0;
            let currentParagraph = null;

            function typeNextChar() {
                if (paraIndex >= paragraphs.length) return;

                const paragraphHtml = paragraphs[paraIndex];

                if (charIndex === 0) {
                    currentParagraph = document.createElement("p");
                    currentParagraph.innerHTML = "";  // 초기화
                    currentParagraph.style.margin = "12px 0";
                    loadingMessage.appendChild(currentParagraph);
                }

// br 태그 감지 후 처리
                if (paragraphHtml.slice(charIndex).startsWith("<br>")) {
                    currentParagraph.appendChild(document.createElement("br"));
                    charIndex += 4; // "<br>" 길이
                    setTimeout(typeNextChar, 20);
                } else if (paragraphHtml.slice(charIndex).startsWith("<br/>")) {
                    currentParagraph.appendChild(document.createElement("br"));
                    charIndex += 5; // "<br/>" 길이
                    setTimeout(typeNextChar, 20);
                } else {
                    // 일반 문자 출력
                    const char = paragraphHtml[charIndex];
                    currentParagraph.innerHTML += char === " " ? "&nbsp;" : char;
                    charIndex++;
                    messages.scrollTop = messages.scrollHeight;
                    setTimeout(typeNextChar, 20);
                }

                // 문단 끝나면 다음으로
                if (charIndex >= paragraphHtml.length) {
                    charIndex = 0;
                    paraIndex++;
                    setTimeout(typeNextChar, 300);
                }
            }

            typeNextChar();

        } catch (err) {
            console.error("메시지 전송 실패:", err);
        }

    }

// [7] 모달
    // 모달 열기 함수
    function openModal() {
        modalOverlay.style.display = "flex"; // 모달창을 화면에 보이게
        modalInput.focus();
    }

    // 모달 닫기 함수
    function closeModal() {
        modalOverlay.style.display = "none";
    }

    // 모달 닫기
    modalCancel.addEventListener("click", closeModal);

    // 모달 열기
    newChatBtn.addEventListener("click", openModal);

    // 모달 제목 수정 (엔터, 클릭 모두 허용)
    async function handleModalSubmit() {
        const inputTitle = modalInput.value.trim();

        if (!inputTitle) {
            alert("제목을 입력하세요!");
            modalInput.focus();
            return;
        }

        try {

            if (editingChatItem) {
                // 편집 모드: 기존 채팅방 제목 수정
                const croomIdx = editingChatItem.dataset.croomIdx;

                const response = await fetch(`/chat/update/${croomIdx}`, {
                    method: "PUT",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({title: inputTitle})
                })

                if (!response.ok) throw new Error("수정 실패");

                // UI 업데이트 (바로 반영)
                const nameEl = editingChatItem.querySelector(".chat-name");
                nameEl.textContent = inputTitle;

                // 현재 선택된 채팅방이면, 헤더도 바꿔야 함
                if (chatTitle.dataset.croomIdx == croomIdx) {
                    chatTitle.textContent = inputTitle;
                    chatTitle.dataset.croomIdx = croomIdx;
                }

            } else { // 없는경우 새 채팅방 생성

                const newRoom = await createChatRoom(inputTitle);

                // 기존 목록은 유지하면서 새 채팅방만 위에 추가
                const newItem = createChatItem(newRoom.croomTitle, newRoom.croomIdx);
                chatList.prepend(newItem);

            }

            closeModal();
            modalInput.value = ""; // 모달 입력 초기화
            editingChatItem = null;

        } catch (error) {
            alert("채팅방 생성 실패: " + error.message);
        }
    }

// 모달 확인 버튼 클릭 시
    modalOk.addEventListener("click", handleModalSubmit);

// 엔터키 입력 시 (모달 input에서)
    modalInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault(); // 혹시 기본 동작 방지
            handleModalSubmit().catch(err => console.log(err.message));
        }
    });

// 채팅방 생성 함수
    async function createChatRoom(title) {

        const response = await fetch("/chat/create", {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title})
        });

        const newRoom = await response.json();
        currentChatRoomIdx = newRoom.croomIdx;

        return newRoom;
    }

})
;