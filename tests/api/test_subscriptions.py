import pytest


@pytest.mark.asyncio
async def test_create_subscription_success(client, test_user, test_active_promotion):
    """Test POST /subscriptions - success case."""
    response = await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_active_promotion.id,
            "metadata": {"source": "web"}
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["promotion_id"] == test_active_promotion.id
    assert data["is_active"] is True
    assert data["metadata"] == {"source": "web"}
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_subscription_user_not_found(client, test_active_promotion):
    """Test POST /subscriptions - fails when user doesn't exist."""
    response = await client.post(
        "/subscriptions",
        json={
            "user_id": 999,
            "promotion_id": test_active_promotion.id
        }
    )

    assert response.status_code == 404
    assert "User 999 not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_subscription_promotion_not_active(client, test_user, test_draft_promotion):
    """Test POST /subscriptions - fails when promotion is DRAFT."""
    response = await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_draft_promotion.id
        }
    )

    assert response.status_code == 422
    assert "ACTIVE" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_subscription_duplicate(client, test_user, test_active_promotion):
    """Test POST /subscriptions - fails on duplicate."""
    # Create first subscription
    response1 = await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_active_promotion.id
        }
    )
    assert response1.status_code == 201

    # Attempt duplicate
    response2 = await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_active_promotion.id
        }
    )
    assert response2.status_code == 409
    assert "already subscribed" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_subscriptions_by_user(client, test_user, test_active_promotion):
    """Test GET /subscriptions?user_id=X."""
    # Create subscription
    await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_active_promotion.id
        }
    )

    # List subscriptions
    response = await client.get(f"/subscriptions?user_id={test_user.id}")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_list_subscriptions_by_promotion(client, test_user, test_active_promotion):
    """Test GET /subscriptions?promotion_id=X."""
    # Create subscription
    await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_active_promotion.id
        }
    )

    # List subscriptions
    response = await client.get(f"/subscriptions?promotion_id={test_active_promotion.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["promotion_id"] == test_active_promotion.id


@pytest.mark.asyncio
async def test_list_subscriptions_filter_by_active(client, test_user, test_active_promotion):
    """Test GET /subscriptions with is_active filter."""
    # Create subscription
    create_response = await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_active_promotion.id
        }
    )
    subscription_id = create_response.json()["id"]

    # Deactivate it
    await client.patch(f"/subscriptions/{subscription_id}/deactivate")

    # List only active subscriptions
    response = await client.get(f"/subscriptions?user_id={test_user.id}&is_active=true")
    assert response.status_code == 200
    assert response.json()["total"] == 0

    # List only inactive subscriptions
    response = await client.get(f"/subscriptions?user_id={test_user.id}&is_active=false")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_subscriptions_missing_filter(client):
    """Test GET /subscriptions - fails without user_id or promotion_id."""
    response = await client.get("/subscriptions")

    assert response.status_code == 422
    assert "user_id or promotion_id" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_subscriptions_both_filters(client):
    """Test GET /subscriptions - fails with both user_id and promotion_id."""
    response = await client.get("/subscriptions?user_id=1&promotion_id=1")

    assert response.status_code == 422
    assert "both" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_subscriptions_pagination(client, test_user, db_session):
    """Test GET /subscriptions pagination."""
    from promopulse.db.models.promotion import Promotion, PromotionStatus
    from datetime import datetime, timezone

    # Create multiple promotions and subscriptions
    for i in range(5):
        promo = Promotion(
            name=f"Promo {i}",
            status=PromotionStatus.ACTIVE,
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc),
            created_by=test_user.id
        )
        db_session.add(promo)
        await db_session.commit()
        await db_session.refresh(promo)

        await client.post(
            "/subscriptions",
            json={
                "user_id": test_user.id,
                "promotion_id": promo.id
            }
        )

    # Test pagination
    response = await client.get(f"/subscriptions?user_id={test_user.id}&limit=3&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5

    response = await client.get(f"/subscriptions?user_id={test_user.id}&limit=3&offset=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_deactivate_subscription(client, test_user, test_active_promotion):
    """Test PATCH /subscriptions/{id}/deactivate."""
    # Create subscription
    create_response = await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_active_promotion.id
        }
    )
    subscription_id = create_response.json()["id"]

    # Deactivate
    response = await client.patch(f"/subscriptions/{subscription_id}/deactivate")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == subscription_id
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_deactivate_subscription_not_found(client):
    """Test PATCH /subscriptions/{id}/deactivate - not found."""
    response = await client.patch("/subscriptions/99999/deactivate")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deactivate_subscription_already_inactive(client, test_user, test_active_promotion):
    """Test PATCH /subscriptions/{id}/deactivate - already inactive."""
    # Create and deactivate subscription
    create_response = await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": test_active_promotion.id
        }
    )
    subscription_id = create_response.json()["id"]
    await client.patch(f"/subscriptions/{subscription_id}/deactivate")

    # Attempt to deactivate again
    response = await client.patch(f"/subscriptions/{subscription_id}/deactivate")

    assert response.status_code == 422
    assert "already inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_subscription_invalid_user_id(client, test_active_promotion):
    """Test POST /subscriptions - validation for invalid user_id."""
    response = await client.post(
        "/subscriptions",
        json={
            "user_id": -1,
            "promotion_id": test_active_promotion.id
        }
    )

    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_create_subscription_invalid_promotion_id(client, test_user):
    """Test POST /subscriptions - validation for invalid promotion_id."""
    response = await client.post(
        "/subscriptions",
        json={
            "user_id": test_user.id,
            "promotion_id": 0
        }
    )

    assert response.status_code == 422  # Pydantic validation error
