package com.project.demo.Service;

import com.project.demo.Model.Chat;
import com.project.demo.Model.ChatRoom;
import com.project.demo.Model.User;
import com.project.demo.Repository.ChatRepository;
import com.project.demo.Repository.ChatRoomRepository;
import com.project.demo.Repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpEntity;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class ChatApiService {

    private final ChatRepository chatRepository;
    private final ChatRoomRepository chatRoomRepository;
    private final UserRepository userRepository;

    // FastAPI 보내는 URL 주소 및 요청 Template
    private final RestTemplate restTemplate = new RestTemplate();
    private final String fastApiBaseUrl = "http://127.0.0.1:8002/chat";

    // 사용자 메시지 저장, chatBot 응답
    @Transactional
    public Map<String, Object> sendAndSave(Chat chat) {

        // 1. 채팅방 존재 확인 (ChatRoom 객체 필요 없음, 단순 확인용)
        Integer croomIdx = chat.getCroomIdx();
        chatRoomRepository.findById(croomIdx)
                .orElseThrow(() -> new IllegalArgumentException("채팅방이 없습니다."));

        // 2. 사용자 메시지 저장
        if (chat.getCreatedAt() == null) {
            chat.setCreatedAt(LocalDateTime.now());
        }
        chatRepository.save(chat);

        // 3. 유저정보 조회!
        Integer userIdx = Integer.parseInt(chat.getChatter());
        User user = userRepository.findById(userIdx)
                .orElseThrow(() -> new IllegalArgumentException("해당 유저 없음"));

        // 3. FastAPI 요청 데이터 구성
        Map<String, Object> request = new HashMap<>();
        request.put("message", chat.getChat());
        request.put("croomIdx", chat.getCroomIdx());
        request.put("chatter", chat.getChatter());
        request.put("createdAt", chat.getCreatedAt().toString());

        Map<String, String> userMeta = new HashMap<>();
        userMeta.put("name", user.getUserName());
        userMeta.put("years", user.getUserYears());
        userMeta.put("location", user.getUserLocation());
        userMeta.put("employees", user.getUserEmployees());
        userMeta.put("sales", user.getUserSalesRange());
        userMeta.put("industry", user.getUserIndustry());

        request.put("userMeta", userMeta);

        // ✅ 기업 유형 (List<String>)도 함께 전송
        request.put("userTypes", user.getUserTypes());

        System.out.println(request);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        // 요청 데이터는 JSON 형태라고 서버에 알려줌
        
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);
        // HttpEntity: HTTP 요청의 본문(body) 와 headers를 묶은 객체
        
        
        // 4. FastAPI로 요청 전송
        ResponseEntity<Map> response = restTemplate.postForEntity(fastApiBaseUrl, entity, Map.class);
        // entity: 보낼 데이터 + 헤더
        // Map.class : 응답을 Map 타입으로 받겠다.

        // ResponseEntity<Map> response: HTTP 응답의 상태 코드 + 헤더 + 본문을 포함
        // [1] response.getStatusCode()  // 200 (성공)
        // [2] response.getHeaders()
            // Content-Type: application/json
            // Content-Length: 150
            // Date: 2024-01-01T10:00:00Z
            // 등등...
        // [3] response.getBody()
            // {
            //  "response": "추천 지원사업은 다음과 같습니다...",
            //   "croomIdx": 123,
            //   "chatter": "ChatBot",
            //   "createdAt": "2024-01-01T10:00:00Z"
            // }

        Map<String, Object> responseBody = response.getBody();
        System.out.println("FastAPI 응답: " + responseBody);

        String responseContent = (String) responseBody.get("response");

        // 5. 응답 메시지 저장
        Chat responseMessage = new Chat();
        responseMessage.setCroomIdx(croomIdx);
        responseMessage.setChat(responseContent);
        responseMessage.setChatter("ChatBot");
        responseMessage.setRatings("5");

        Chat savedResponse = chatRepository.save(responseMessage);

        // 6. Map으로 변환
        // Map으로 변환
        Map<String, Object> result = new HashMap<>();
        result.put("chatIdx", savedResponse.getChatIdx());
        result.put("croomIdx", savedResponse.getCroomIdx());
        result.put("chatter", savedResponse.getChatter());
        result.put("chat", savedResponse.getChat());
        result.put("ratings", savedResponse.getRatings());
        result.put("createdAt", savedResponse.getCreatedAt().toString());

        return result;

    }
}
