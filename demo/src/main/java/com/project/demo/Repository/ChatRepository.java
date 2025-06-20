package com.project.demo.Repository;

import com.project.demo.Model.Chat;
import com.project.demo.Model.ChatRoom;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChatRepository extends JpaRepository<Chat, Integer> {

    // 특정 채팅방(croomIdx)의 메시지를 시간순으로 정렬하여 반환
    List<Chat> findByCroomIdxOrderByCreatedAtAsc(Integer croomIdx);

}
