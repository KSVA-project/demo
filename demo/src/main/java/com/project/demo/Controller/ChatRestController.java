package com.project.demo.Controller;

import com.project.demo.Model.Chat;
import com.project.demo.Model.ChatRoom;
import com.project.demo.Service.ChatRoomService;
import com.project.demo.Service.ChatService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/chat")
@RequiredArgsConstructor
public class ChatRestController {

    private final ChatRoomService chatRoomService;
    private final ChatService chatService;

    // [1] 채팅방 목록을 불러옴
    @GetMapping("/{userIdx}")
    public ResponseEntity<List<Map<String, Object>>> getChatRooms(@PathVariable int userIdx) {

        List<ChatRoom> chatRooms = chatRoomService.getChatRoomsByEmail(userIdx);

        // Map 리스트로 변환
        List<Map<String, Object>> result = new ArrayList<>();

        for (ChatRoom room : chatRooms) {
            Map<String, Object> map = new HashMap<>();
            map.put("croomIdx", room.getCroomIdx());
            map.put("croomTitle", room.getCroomTitle());
            result.add(map);
        }

        return ResponseEntity.ok(result);
    }

    // [2] 채팅방 생성
    @PostMapping("/create")
    public ResponseEntity<?> createChatRoom(@RequestBody Map<String, String> requestBody, HttpSession session) {

        String title = requestBody.get("title");
        Integer userIdx = (Integer) session.getAttribute("userIdx");

        if (userIdx == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("로그인이 필요합니다.");
        }

        ChatRoom newRoom = chatRoomService.createChatRoom(title, userIdx);
        Map<String, Object> response = new HashMap<>();
        response.put("croomIdx", newRoom.getCroomIdx());
        response.put("croomTitle", newRoom.getCroomTitle());

        return ResponseEntity.ok(response);
    }

    // [3] 채팅방 삭제
    @GetMapping("/delete/{croomIdx}")
    public ResponseEntity<?> getChatRoom(@PathVariable int croomIdx) {

        chatRoomService.deleteChatRoom(croomIdx);

        return ResponseEntity.ok().build();
    }

    // [4] 채팅방 메시지 랜더링
    @GetMapping("/messages/{croomIdx}")
    public ResponseEntity<List<Map<String, Object>>> getChatRoomMessages(@PathVariable int croomIdx) {

        List<Map<String, Object>> messages = chatService.getChatsByRoomIdx(croomIdx);

        return ResponseEntity.ok(messages);
    }

    // [5] 채팅방 제목 수정 (더블클릭)
    @PutMapping("/update/{croomIdx}")
    public ResponseEntity<?> updateChatRoom(@PathVariable int croomIdx, @RequestBody Map<String, String> requestBody) {

        String newTitle = requestBody.get("title");

        chatRoomService.updateTitle(croomIdx, newTitle);

        return ResponseEntity.ok(Map.of(
                "croomIdx", croomIdx,
                "croomTitle", newTitle
        ));
    }

}
