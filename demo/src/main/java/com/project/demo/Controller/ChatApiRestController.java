package com.project.demo.Controller;

import com.project.demo.Model.Chat;
import com.project.demo.Service.ChatApiService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatApiRestController {

    private final ChatApiService chatApiService;

    @PostMapping("/message")
    public ResponseEntity<?> sendMessageTOFastAPI(@RequestBody Chat chat) {

        try {
            Map<String, Object> botReply = chatApiService.sendAndSave(chat);
            return ResponseEntity.ok(botReply);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500).body("FastAPI 통신 중 오류 발생");
        }


    }

}
