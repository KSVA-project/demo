package com.project.demo.Repository;

import com.project.demo.Model.Chat;
import com.project.demo.Model.ChatRoom;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChatRepository extends JpaRepository<Chat, Integer> {

    // 특정 채팅방(croomIdx)의 메시지를 시간순으로 정렬하여 반환
    List<Chat> findByChatRoomOrderByCreatedAtAsc(ChatRoom chatRoom);
    // @ManyToOne으로 ChatRoom을 참조하고 있기 때문에 chatRoom 객체로 탐색

}
