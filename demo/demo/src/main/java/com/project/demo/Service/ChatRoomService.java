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

    // 채팅 목록 불러오기
    public List<ChatRoom> getChatRoomsByUserIdx(int userIdx) {
        return chatRoomRepository.findByUserIdx(userIdx);
    }

    // 채팅방 만들기
    public ChatRoom createChatRoom(String title, Integer userIdx) {
        // user 필드는 @ManyToOne(fetch = FetchType.LAZY)로
        // 실제 DB에는 USER_IDX라는 외래키 컬럼으로 저장됨.
        // 연관된 Entitiy 객체를 넣어줘야 외래키가 자동으로 관리되고, 저장되어야 함.

        ChatRoom chatRoom = new ChatRoom();
        chatRoom.setCroomTitle(title);
        chatRoom.setUserIdx(userIdx);
        chatRoom.setCreatedAt(LocalDateTime.now());

        return chatRoomRepository.save(chatRoom);
    }

    // 채팅방 삭제로직
    public void deleteChatRoom(Integer croomIdx) {
        chatRoomRepository.deleteById(croomIdx);
    }

    // 채팅방 제목 변경
    @Transactional
    public void updateTitle(int croomIdx, String newTitle) {
        
        // 존재 여부만 확인
        chatRoomRepository.findById(croomIdx)
                .orElseThrow(() -> new IllegalArgumentException("채팅방이 존재하지 않음 id=" + croomIdx));

        // 제목 업데이트
        chatRoomRepository.updateTitle(croomIdx, newTitle);
    }
}
