package com.project.demo.Service;

import com.project.demo.Model.Chat;
import com.project.demo.Model.ChatRoom;
import com.project.demo.Repository.ChatRepository;
import com.project.demo.Repository.ChatRoomRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class ChatService {

    private final ChatRepository chatRepository;
    private final ChatRoomRepository chatRoomRepository;

    public List<Map<String, Object>> getChatsByRoomIdx(Integer croomIdx) {

        ChatRoom chatRoom = chatRoomRepository.findById(croomIdx)
                .orElseThrow(() -> new IllegalArgumentException("해당 채팅방이 존재하지 않습니다: " + croomIdx));

        List<Chat> chatList = chatRepository.findByChatRoomOrderByCreatedAtAsc(chatRoom);

        List<Map<String, Object>> result = new ArrayList<>();

        for (Chat chat : chatList) {
            Map<String, Object> map = new HashMap<String, Object>();
            map.put("chatIdx", chat.getChatIdx()); // 채팅 식별자
            map.put("chatter",chat.getChatter()); // 발화자
            map.put("chat", chat.getChat()); // 채팅내용
            map.put("ratings", chat.getRatings());
            map.put("createdAt", chat.getCreatedAt().toString());
            result.add(map);
        }

        return result;
    }


}
