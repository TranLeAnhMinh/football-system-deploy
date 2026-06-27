package com.example.footballmanagement.repository;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import com.example.footballmanagement.entity.PriceRule;

@Repository
public interface PriceRuleRepository extends JpaRepository<PriceRule, UUID> {

    @Query("""
        SELECT r
        FROM PriceRule r
        WHERE r.active = true
          AND (r.pitch.id = :pitchId OR r.pitch IS NULL)
          AND (r.validFrom IS NULL OR r.validFrom <= :date)
          AND (r.validTo IS NULL OR r.validTo >= :date)
        ORDER BY r.priority ASC
    """)
    List<PriceRule> findValidRules(UUID pitchId, LocalDate date);

    @Query("""
        SELECT r
        FROM PriceRule r
        WHERE (:active IS NULL OR r.active = :active)
          AND (:pitchId IS NULL OR r.pitch.id = :pitchId)
        ORDER BY r.priority ASC, r.createdAt DESC
    """)
    Page<PriceRule> findForAdmin(UUID pitchId, Boolean active, Pageable pageable);
}