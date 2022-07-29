package main

import (
	"fmt"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/slack-go/slack"
)

func main() {
	r := gin.Default()
	r.GET("/slack", slackHandler)
	port := os.Getenv("PORT")
	if len(port) == 0 {
		port = "8080"
	}
	r.Run(fmt.Sprintf(":%s", port))
}

// Handle slack
func slackHandler(c *gin.Context) {
	// Get message parameter from query
	message := c.Query("message")
	// Throw error if message is empty
	if message == "" {
		c.String(http.StatusBadRequest, "Query parameter `message` is empty")
		return
	}
	// Get channel parameter from query
	channel := c.Query("channel")
	// Throw error if channel is empty
	if channel == "" {
		c.String(http.StatusBadRequest, "Query parameter `channel` is empty")
		return
	}
	// Get token from environment variable
	token := os.Getenv("SLACK_TOKEN")
	// Throw error if token is empty
	if token == "" {
		c.String(http.StatusBadRequest, "Environment variable `SLACK_TOKEN` is empty")
		return
	}
	// Send message to Slack
	api := slack.New(token)
	_, _, err := api.PostMessage(channel, slack.MsgOptionText(message, false))
	// Throw error if message could not be sent
	if err != nil {
		c.String(http.StatusInternalServerError, err.Error())
		return
	}
	// Return success
	c.String(http.StatusOK, "Success")
}
