package com.project.demo.Service;

import com.project.demo.Model.ChatRoom;
import com.project.demo.Model.User;
import com.project.demo.Repository.ChatRoomRepository;
import com.project.demo.Repository.UserRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ChatRoomService {

    private final ChatRoomRepository chatRoomRepository;
    private final UserRepository userRepository;

    // 채팅 목록 불러오기
    public List<ChatRoom> getChatRoomsByEmail(int userIdx) {

        User user = userRepository.findById(userIdx).orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다:" + userIdx));
        return chatRoomRepository.findByUser(user);
    }


    // 채팅방 만들기
    public ChatRoom createChatRoom(String title, Integer userIdx) {
        // user 필드는 @ManyToOne(fetch = FetchType.LAZY)로
        // 실제 DB에는 USER_IDX라는 외래키 컬럼으로 저장됨.
        // 연관된 Entitiy 객체를 넣어줘야 외래키가 자동으로 관리되고, 저장되어야 함.

        User user = userRepository.findById(userIdx)
                .orElseThrow(() -> new IllegalArgumentException("유저가 없습니다. userIdx=" + userIdx));

        ChatRoom chatRoom = new ChatRoom();
        chatRoom.setCroomTitle(title);
        chatRoom.setUser(user);
        chatRoom.setCreatedAt(LocalDateTime.now());

        return chatRoomRepository.save(chatRoom);
    }

    // 채팅방 삭제로직
    public void deleteChatRoom(int croomIdx) {
        chatRoomRepository.deleteById(croomIdx);
    }

    // 채팅방 제목 변경
    @Transactional
    public void updateTitle(int croomIdx, String newTitle) {
        
        ChatRoom chatRoom = chatRoomRepository.findById(croomIdx)
                .orElseThrow(() -> new IllegalArgumentException("채팅방이 존재하지 않음 id=" + croomIdx));
        chatRoomRepository.updateTitle(croomIdx, newTitle);
    }
}
