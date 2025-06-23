document.addEventListener("DOMContentLoaded", () => {

        // 채팅 메시지 전송
        const sendBtn = document.getElementById("sendBtn"); // 보내기 버튼
        const userInput = document.getElementById("userInput"); // 유저 입력값
        sendBtn.addEventListener("click", sendMessage);

        function autoResize() {
            userInput.style.height = "44px";
            const scrollHeight = userInput.scrollHeight;
            const maxHeight = 104;
            if (scrollHeight <= maxHeight) {
                userInput.style.height = scrollHeight + "px";
                userInput.classList.remove("scrollable");
            } else {
                userInput.style.height = maxHeight + "px";
                userInput.classList.add("scrollable");
            }
        }

        userInput.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.stopImmediatePropagation();
                    if (!e.shiftKey) {
                        e.preventDefault();
                        sendBtn.click();
                    }
                    // Shift+Enter는 preventDefault 하지 않으므로 기본 줄바꿈만 일어남
                }
            },
            true
        );

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
            userInput.addEventListener("input", autoResize);
            autoResize();
            loadChatRooms();
        }

        init();


        /*
        📚 전체 구조 이해하기:
        1. 사용자가 메시지 입력 → sendMessage() 함수 실행
        2. 서버에서 챗봇 응답받음 → 타이핑 애니메이션으로 한 글자씩 출력
        3. 타이핑 중에 링크 발견 → 클릭 가능한 링크로 변환
        4. 사용자가 이전 채팅 선택 → selectChat() 함수로 기존 메시지 렌더링
        5. 기존 메시지 렌더링할 때도 링크 처리
        핵심: "텍스트에서 링크를 찾아서 클릭 가능하게 만들기"
        */

        // 🔗 링크 요소 생성 함수
        function createRenderLink(linkText, linkUrl) {
            /*
            이 함수의 역할: 클릭 가능한 링크 HTML 요소를 만들기
            - linkText: 화면에 보여질 텍스트 (예: "링크", "네이버")
            - linkUrl: 실제 이동할 URL 주소 (예: "https://naver.com")
            반환값: 완성된 <a> 태그 DOM 요소
            */
            const linkElement = document.createElement("a");
            linkElement.href = linkUrl.trim();
            // 링크 주소 지정
            linkElement.textContent = linkText; //텍스트 지정
            linkElement.style.color = "#007bff"; // 링크 색
            linkElement.style.textDecoration = "underline"; // 밑줄
            linkElement.style.cursor = "pointer"; // 마우스 오버 시 손모양 커서
            linkElement.target = "_blank";  // 새창 열기

            // 클릭 이벤트 추가
            addLinkClickEvent(linkElement);

            return linkElement;
        }

        // ===============================================
        // 🖱️ 링크 클릭 이벤트 함수 (재사용 가능)
        function addLinkClickEvent(linkElement) {
            /*
            링크에 클릭 이벤트와 호버 효과를 추가
            - linkElement: 위에서 만든 <a> 태그 요소
            */
            linkElement.addEventListener('click', function (e) {

                e.preventDefault(); // 기본 동작 중단 (기존 <a> 링크 클릭 무효화)
                const url = this.href || this.getAttribute('href'); // 링크 주소 가져오기

                // Referrer 없이 새 창 열기 (기업마당 사이트 접근 문제 해결)
                const newWindow = window.open('about:blank', '_blank');
                // 1. 빈 페이지('about:blank')를 먼저 새 창에서 열기
                // 2. 그 창에서 원하는 주소로 이동
                newWindow.location.href = url;
            });

            // 🎨 마우스 올렸을 때 호버 효과
            linkElement.addEventListener('mouseenter', function () {
                this.style.backgroundColor = 'rgba(0, 123, 255, 0.1)';
            });
            linkElement.addEventListener('mouseleave', function () {
                this.style.backgroundColor = 'transparent';
            });
        }

        // ===============================================
        // 🔗 텍스트에서 링크 처리하는 함수
        function processLinksInText(text) {
            const container = document.createDocumentFragment();
            let currentIndex = 0;

            while (currentIndex < text.length) {
                let foundPattern = false;
                const remainingText = text.slice(currentIndex);

                // 🔗 1. 마크다운 링크 [텍스트](URL)
                const markdownLinkRegex = /^\[([^\]]*)\]\(([^)]+)\)/;
                const markdownLinkMatch = remainingText.match(markdownLinkRegex);

                if (markdownLinkMatch) {
                    const linkText = markdownLinkMatch[1];
                    const linkUrl = markdownLinkMatch[2];
                    const linkElement = createRenderLink(linkText, linkUrl);
                    container.appendChild(linkElement);
                    currentIndex += markdownLinkMatch[0].length;
                    foundPattern = true;
                }

                // 🏷️ 2. HTML <a> 태그
                else if (remainingText.startsWith('<a ')) {
                    const endIdx = text.indexOf('</a>', currentIndex);
                    if (endIdx !== -1) {
                        const linkHtml = text.slice(currentIndex, endIdx + 4);
                        const temp = document.createElement('div');
                        temp.innerHTML = linkHtml;
                        const linkNode = temp.firstChild;
                        addLinkClickEvent(linkNode);
                        container.appendChild(linkNode);
                        currentIndex = endIdx + 4;
                        foundPattern = true;
                    }
                }

                // 💪 3. 볼드 **텍스트** - 수정된 버전!
                else if (remainingText.startsWith('**')) {
                    const boldRegex = /^\*\*([^*]+)\*\*/;
                    const boldMatch = remainingText.match(boldRegex);

                    if (boldMatch) {
                        const boldText = boldMatch[1];

                        // 볼드 요소 만들기
                        const strongElement = document.createElement('strong');
                        strongElement.textContent = boldText;
                        strongElement.style.cssText = `
                    font-weight: 900 !important;
                    color: #000 !important;
                `;

                        container.appendChild(strongElement);
                        currentIndex += boldMatch[0].length;
                        foundPattern = true;
                    }
                }

                // 🔗 4. 일반 URL
                else if (remainingText.match(/^https?:\/\/[^\s<>")\]]+/)) {
                    const urlRegex = /^(https?:\/\/[^\s<>")\]]+)/;
                    const urlMatch = remainingText.match(urlRegex);

                    if (urlMatch) {
                        const url = urlMatch[0];
                        const linkElement = createRenderLink(url, url);
                        container.appendChild(linkElement);
                        currentIndex += url.length;
                        foundPattern = true;
                    }
                }

                // 🔄 5. <br> 태그
                else if (remainingText.startsWith('<br>')) {
                    container.appendChild(document.createElement('br'));
                    currentIndex += 4;
                    foundPattern = true;
                } else if (remainingText.startsWith('<br/>')) {
                    container.appendChild(document.createElement('br'));
                    currentIndex += 5;
                    foundPattern = true;
                }

                // 📄 6. 일반 텍스트
                if (!foundPattern) {
                    const char = text[currentIndex]; // 현재 텍스트 위치의 한개만 꺼냅
                    const textNode = document.createTextNode(char === ' ' ? '\u00A0' : char);
                    // \u00A0는 non-breaking space (줄바꿈이 되지 않고, 유지됨)
                    container.appendChild(textNode);
                    currentIndex++;
                }
            }

            return container;
        }

        // [2] 채팅방 목록 불러오기 함수
        async function loadChatRooms() {

            const userIdx = sessionStorage.getItem("userIdx");
            if (!userIdx) {
                return;
            }

            try {
                const response = await fetch(`/chat/${userIdx}`);
                if (!response.ok) throw new Error("응답 실패");

                const chatRooms = await response.json(); // 한 번만 호출
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

            // 제목 span
            const nameSpan = document.createElement("span");
            nameSpan.className = "chat-name";
            nameSpan.textContent = title;

            // 삭제 버튼
            const delBtn = document.createElement("span");
            delBtn.className = "delete-btn";
            delBtn.textContent = "X";

            item.append(nameSpan, delBtn);

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

            // 🔥 [호버 유지 효과: active 클래스 제어]
            const chatItems = document.querySelectorAll(".chat-item");
            chatItems.forEach(item => item.classList.remove("active")); // 기존 active 제거

            const selectedItem = [...chatItems].find(item => item.dataset.croomIdx === String(croomIdx));
            if (selectedItem) {
                selectedItem.classList.add("active"); // 현재 선택한 항목에 active 추가
            }

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

                                // 🔥 링크 처리 추가!
                                const processedContent = processLinksInText(p.trim());
                                para.appendChild(processedContent);

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

                // 1. <br> 또는 <br/>이 2개 연속된 구간을 기준으로 문단 단위로 나눔
                const paragraphs = rawReply.split(/<br\s*\/?>\s*<br\s*\/?>/i);

                let paraIndex = 0;        // 현재 몇 번째 문단인지
                let charIndex = 0;        // 문단 내에서 몇 번째 문자까지 타이핑했는지
                let currentParagraph = null;  // 현재 <p> 태그 DOM 객체

                // 재귀 함수: 함수에서 자기 자신을 다시 호출해 작업을 수행하는 방식
                function typeNextChar() {
                    if (paraIndex >= paragraphs.length) return;

                    const paragraphHtml = paragraphs[paraIndex];

                    if (charIndex === 0) {
                        currentParagraph = document.createElement("p");
                        currentParagraph.innerHTML = "";
                        currentParagraph.style.margin = "12px 0";
                        loadingMessage.appendChild(currentParagraph);
                    }

                    const remainingText = paragraphHtml.slice(charIndex);

                    // [1] <br> 태그 처리 - 기존 유지
                    if (remainingText.startsWith("<br>")) {
                        currentParagraph.appendChild(document.createElement("br"));
                        charIndex += 4;
                        setTimeout(typeNextChar, 20);
                        return;
                    }

                    if (remainingText.startsWith("<br/>")) {
                        currentParagraph.appendChild(document.createElement("br"));
                        charIndex += 5;
                        setTimeout(typeNextChar, 20);
                        return;
                    }

                    // [2] <a> 태그 처리 - 기존 유지
                    if (remainingText.startsWith("<a ")) {
                        const endIdx = paragraphHtml.indexOf("</a>", charIndex);
                        if (endIdx !== -1) {
                            const linkHtml = paragraphHtml.slice(charIndex, endIdx + 4);
                            const temp = document.createElement("div");
                            temp.innerHTML = linkHtml;
                            const linkNode = temp.firstChild;
                            addLinkClickEvent(linkNode);
                            currentParagraph.appendChild(linkNode);
                            charIndex = endIdx + 4;
                            messages.scrollTop = messages.scrollHeight;
                            setTimeout(typeNextChar, 50);
                            return;
                        }
                    }

                    // [3] 마크다운 링크 처리 - 기존 유지
                    const markdownLinkRegex = /^\[([^\]]*)\]\(([^)]+)\)/;
                    const markdownMatch = remainingText.match(markdownLinkRegex);

                    if (markdownMatch) {
                        const linkText = markdownMatch[1];
                        const linkUrl = markdownMatch[2];
                        const linkElement = createRenderLink(linkText, linkUrl.trim());
                        currentParagraph.appendChild(linkElement);
                        charIndex += markdownMatch[0].length;
                        messages.scrollTop = messages.scrollHeight;
                        setTimeout(typeNextChar, 50);
                        return;
                    }

                    // 💪 [4] 볼드 **텍스트** 처리 - 새로 추가!
                    if (remainingText.startsWith('**')) {
                        const boldRegex = /^\*\*([^*]+)\*\*/;
                        const boldMatch = remainingText.match(boldRegex);

                        if (boldMatch) {
                            const boldText = boldMatch[1]; // **사이의 텍스트**

                            // 볼드 요소 만들기
                            const strongElement = document.createElement('strong');
                            strongElement.textContent = boldText;
                            strongElement.style.fontWeight = 'bold';

                            currentParagraph.appendChild(strongElement);
                            charIndex += boldMatch[0].length; // **텍스트** 전체 길이만큼 이동

                            messages.scrollTop = messages.scrollHeight;
                            setTimeout(typeNextChar, 30); // 볼드는 조금 빠르게 출력
                            return;
                        }
                    }

                    // [5] 일반 URL 처리 - 기존 유지
                    const urlRegex = /(https?:\/\/[^\s<>")\]]+)/;
                    const urlMatch = remainingText.match(urlRegex);

                    if (urlMatch && remainingText.indexOf(urlMatch[0]) === 0) {
                        const url = urlMatch[0];
                        const linkElement = createRenderLink(url, url);
                        currentParagraph.appendChild(linkElement);
                        charIndex += url.length;
                        messages.scrollTop = messages.scrollHeight;
                        setTimeout(typeNextChar, 50);
                        return;
                    }

                    // [6] 일반 문자 처리 - 기존 유지
                    if (charIndex < paragraphHtml.length) {
                        const char = paragraphHtml[charIndex];

                        // innerHTML 대신 textNode 사용
                        const textNode = document.createTextNode(char === " " ? "\u00A0" : char);
                        currentParagraph.appendChild(textNode);

                        charIndex++;
                        messages.scrollTop = messages.scrollHeight;
                        setTimeout(typeNextChar, 20);
                        return;
                    }

                    // [7] 문단 완료 - 기존 유지
                    if (charIndex >= paragraphHtml.length) {
                        charIndex = 0;
                        paraIndex++;
                        setTimeout(typeNextChar, 300);
                    }
                }

                // ✅ 타이핑 애니메이션 시작!
                typeNextChar();

            } catch (err) {
                console.error("메시지 전송 실패:", err);

                // ✅ 에러 발생시 로딩 메시지 제거
                const loadingMessages = document.querySelectorAll('.message.bot');
                const lastLoading = loadingMessages[loadingMessages.length - 1];
                if (lastLoading && lastLoading.textContent === "답변 생성중 입니다.") {
                    lastLoading.textContent = "오류가 발생했습니다. 다시 시도해주세요.";
                }
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

    }
)
;