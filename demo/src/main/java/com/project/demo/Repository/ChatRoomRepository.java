package com.project.demo.Repository;

import com.project.demo.Model.ChatRoom;
import com.project.demo.Model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ChatRoomRepository extends JpaRepository<ChatRoom, Integer> {

     List<ChatRoom> findByUser(User user);

     // JPQL (Java Persistence Query Language)
     @Modifying  //update/delete 쿼리를 실행할 때 필요
     @Query(value = "UPDATE TB_CHATROOM SET CROOM_TITLE = :title WHERE CROOM_IDX = :id", nativeQuery = true)
     void updateTitle(@Param("id") Integer croomIdx, @Param("title") String newTitle);

     // @Param : JPQL이나 네이티브 쿼리에서 사용하는 파라미터 이름을 명시적으로 지정해 주는 역할

}
