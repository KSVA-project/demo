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
            if (response.ok) {
                const chatRooms = await response.json();

                if (chatRooms.length === 0) {
                    chatList.innerHTML = "<p>채팅방이 없습니다. <br>새 채팅방을 만들어주세요!</p>";
                } else {
                    renderChatRooms(chatRooms);
                }
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

        const nameSpan = document.createElement("span");
        nameSpan.className = "chat-name";
        nameSpan.textContent = title;

        const delBtn = document.createElement("button");
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
                        msgDiv.classList.add("bot");
                    } else {
                        msgDiv.classList.add("user");
                    }

                    msgDiv.textContent = msg.chat;
                    messages.appendChild(msgDiv);
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

                // 새로 만든 채팅방 UI에 추가
                const newItem = createChatItem(roomData.croomTitle, roomData.croomIdx);
                chatList.prepend(newItem);

                // UI도 해당 채팅방이름만 전환
                chatTitle.textContent = roomData.croomTitle;
            }

            // 2. 메시지 전송 및 저장
            const sendMsgRes = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    chatRoom: {croomIdx: currentChatRoomIdx},
                    chatter: currentUserName,
                    chat: text
                })
            });

            // 3. 챗봇 응답 메시지 append
            if (!sendMsgRes.ok) throw new Error("메시지 전송 실패");

            // chatBot 응답 데이터
            const resData = await sendMsgRes.json();

            const botMessage = document.createElement("div");
            botMessage.className = "message bot";
            botMessage.textContent = resData.chat; // 응답 Chat 엔티티의 chat 필드 출력
            messages.appendChild(botMessage);

            setTimeout(() => {
                messages.scrollTop = messages.scrollHeight;
            }, 100);

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

                // UI 업데이트
                editingChatItem.querySelector(".chat-name").textContent = inputTitle;

                if (chatHeader.textContent === editingChatItem.querySelector(".chat-name").textContent) {
                    selectChat(inputTitle, croomIdx);
                }


            } else { // 없는경우 새 채팅방 생성
                const newRoom = await createChatRoom(inputTitle);
                const newItem = createChatItem(newRoom.croomTitle, newRoom.croomIdx);
                
                chatList.prepend(newItem);
                selectChat(newRoom.croomTitle, newRoom.croomIdx);


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